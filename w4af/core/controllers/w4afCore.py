"""
w4afCore.py

Copyright 2006 Andres Riancho

This file is part of w4af, https://w4af.net/ .

w4af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w4af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w4af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""


import os
import sys
import time
import errno
import pprint
import threading
import traceback

import w4af.core.data.parsers.parser_cache as parser_cache
import w4af.core.controllers.output_manager as om

from w4af.core.controllers.threads.threadpool import Pool
from w4af.core.controllers.threads.is_main_thread import is_main_thread
from w4af.core.controllers.threads.monkey_patch_debug import monkey_patch_debug, remove_monkey_patch_debug
from w4af.core.controllers.misc.get_w4af_version import get_w4af_version_minimal
from w4af.core.controllers.core_helpers.profiles import CoreProfiles
from w4af.core.controllers.core_helpers.plugins import CorePlugins
from w4af.core.controllers.core_helpers.target import CoreTarget
from w4af.core.controllers.core_helpers.strategy import CoreStrategy
from w4af.core.controllers.core_helpers.fingerprint_404 import fingerprint_404_singleton
from w4af.core.controllers.core_helpers.exception_handler import ExceptionHandler
from w4af.core.controllers.core_helpers.strategy_observers.disk_space_observer import DiskSpaceObserver
from w4af.core.controllers.core_helpers.strategy_observers.thread_count_observer import ThreadCountObserver
from w4af.core.controllers.core_helpers.strategy_observers.thread_state_observer import ThreadStateObserver
from w4af.core.controllers.core_helpers.status import (CoreStatus,
                                                       STOPPED, RUNNING, PAUSED)
from w4af.core.controllers.output_manager import (fresh_output_manager_inst,
                                                  log_sink_factory)
from w4af.core.controllers.profiling import start_profiling, stop_profiling
from w4af.core.controllers.misc.epoch_to_string import epoch_to_string
from w4af.core.controllers.misc.dns_cache import enable_dns_cache
from w4af.core.controllers.misc.number_generator import consecutive_number_generator
from w4af.core.controllers.misc.home_dir import (create_home_dir,
                                                 verify_dir_has_perm,
                                                 get_home_dir)
from w4af.core.controllers.misc.temp_dir import (create_temp_dir,
                                                 remove_temp_dir,
                                                 TEMP_DIR)
from w4af.core.controllers.exceptions import (BaseFrameworkException,
                                              HTTPRequestException,
                                              ScanMustStopException,
                                              ScanMustStopByUnknownReasonExc,
                                              ScanMustStopByUserRequest)

from w4af.core.data.url.extended_urllib import ExtendedUrllib
from w4af.core.data.kb.knowledge_base import kb
from w4af.core.data.db.dbms import DBMSException


NO_MEMORY_MSG = ('The operating system was unable to allocate memory for'
                 ' the Python interpreter (MemoryError). This usually happens'
                 ' when the OS does not have a mounted swap disk, the'
                 ' hardware where w4af is running has less than 1GB RAM,'
                 ' there are many processes running and consuming memory,'
                 ' or w4af is using more memory than expected.')


class w4afCore(object):
    """
    This is the core of the framework, it calls all plugins, handles exceptions,
    coordinates all the work, creates threads, etc.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    # Note that the number of worker threads might be modified
    # by the extended url library. When errors appear the worker
    # thread number is reduced, when no errors are found the
    # worker thread count is increased to provide more speed.
    #
    # This only makes sense as long as the worker threads are
    # mostly used for sending HTTP requests (which is the case
    # for the current w4af version).
    WORKER_THREADS = 30
    MIN_WORKER_THREADS = 20
    MAX_WORKER_THREADS = 100

    WORKER_INQUEUE_MAX_SIZE = WORKER_THREADS * 20
    WORKER_MAX_TASKS = 20

    def __init__(self):
        """
        Init some variables and files.
        Create the URI opener.
        """
        # Make sure we get a fresh new instance of the output manager
        manager = fresh_output_manager_inst()
        log_sink_factory(manager.get_in_queue())

        # FIXME: In the future, when the output_manager is not an awful
        # singleton anymore, this line should be removed and the output_manager
        # object should take a w4afCore object as a parameter in its __init__
        om.manager.set_w4af_core(self)

        # This is more than just a debug message, it's a way to force the
        # output manager thread to start it's work. I would start that thread
        # on output manager instantiation but there are issues with starting
        # threads at module import time.
        om.out.debug('Created new w4afCore instance: %s' % id(self))

        # Create some directories, do this every time before starting a new
        # scan and before doing any other core init because these are widely
        # used
        self._home_directory()
        self._tmp_directory()
        
        # We want to have only one exception handler instance during the whole
        # w4af process. The data captured by it will be cleared before starting
        # each scan, but we want to keep the same instance after a scan because
        # we'll extract info from it.
        self.exception_handler = ExceptionHandler()
        
        # These are some of the most important moving parts in the w4afCore
        # they basically handle every aspect of the w4af framework. I create
        # these here because they are used by the UIs even before starting a
        # scan.
        self.profiles = CoreProfiles(self)
        self.plugins = CorePlugins(self)
        self.status = CoreStatus(self)
        self.target = CoreTarget()
        self.strategy = CoreStrategy(self)

        # Create the URI opener object
        self.uri_opener = ExtendedUrllib()
        self.uri_opener.set_w4af_core(self)

        # Keep track of first scan to call cleanup or not
        self._first_scan = True

        # Worker pool
        self._worker_pool = None

    def scan_start_hook(self):
        """
        Create directories, threads and consumers required to perform a w4af
        scan. Used both when we init the core and when we want to clear all
        the previous results and state from an old scan and start again.
        
        :return: None
        """
        # Create this again just to clear the internal states
        scans_completed = self.status.scans_completed
        self.status = CoreStatus(self, scans_completed=scans_completed)
        self.status.start()

        start_profiling(self)

        if not self._first_scan:
            self.cleanup()
        
        else:
            # Create some directories, do this every time before starting a new
            # scan and before doing any other core init because these are
            # widely used
            self._home_directory()
            self._tmp_directory()
            
            enable_dns_cache()
        
        # Reset global sequence number generator
        consecutive_number_generator.reset()
               
        # Now that we know we're going to run a new scan, overwrite the old
        # strategy which might still have data stored in it and create a new
        # one  
        self.strategy = CoreStrategy(self)
        self.strategy.add_observer(DiskSpaceObserver())
        self.strategy.add_observer(ThreadCountObserver())
        self.strategy.add_observer(ThreadStateObserver())

        # Init the 404 detection for the whole framework
        fp_404_db = fingerprint_404_singleton(cleanup=True)
        fp_404_db.set_url_opener(self.uri_opener)

    def start(self):
        """
        The user interfaces call this method to start the whole scanning
        process.
        
        @raise: This method raises almost every possible exception, so please
                do your error handling!
        """
        om.out.debug('Called w4afCore.start()')

        self.scan_start_hook()

        try:
            # Just in case the GUI / Console forgot to do this...
            self.verify_environment()
        except Exception as e:
            error = ('verify_environment() raised an exception: "%s". This'
                     ' should never happen. Are you (UI developer) sure that'
                     ' you called verify_environment() *before* start() ?')
            om.out.error(error % e)
            raise

        # Let the output plugins know what kind of plugins we're
        # using during the scan
        om.manager.log_enabled_plugins(self.plugins.get_all_enabled_plugins(),
                                       self.plugins.get_all_plugin_options())

        self._first_scan = False

        om.out.debug('Starting the scan using w4af version %s' % get_w4af_version_minimal())

        try:
            self.strategy.start()
        except MemoryError:
            print(NO_MEMORY_MSG)
            om.out.error(NO_MEMORY_MSG)

        except OSError as os_err:
            # https://github.com/andresriancho/w3af/issues/10186
            # OSError: [Errno 12] Cannot allocate memory
            if os_err.errno == errno.ENOMEM:
                print(NO_MEMORY_MSG)
                om.out.error(NO_MEMORY_MSG)
            else:
                raise

        except IOError as io_err:
            (error_id, error_msg) = io_err.args

            # https://github.com/andresriancho/w3af/issues/9653
            # IOError: [Errno 28] No space left on device
            if error_id == errno.ENOSPC:
                msg = ('The w4af scan will stop because the file system'
                       ' is running low on free space. Check the "%s" directory'
                       ' size, overall disk usage and start the scan again.')
                msg %= get_home_dir()

                print(msg)
                om.out.error(msg)
            else:
                raise

        except threading.ThreadError as te:
            handle_threading_error(self.status.scans_completed, te)

        except HTTPRequestException as hre:
            # TODO: These exceptions should never reach this level
            #       adding the exception handler to raise them and fix any
            #       instances where it happens.
            raise

        except ScanMustStopByUserRequest as sbur:
            # I don't have to do anything here, since the user is the one that
            # requested the scanner to stop. From here the code continues at the
            # "finally" clause, which simply shows a message saying that the
            # scan finished.
            om.out.information('%s' % sbur)

        except ScanMustStopByUnknownReasonExc:
            #
            # If the extended_urllib module raises this type of exception we'll
            # just re-raise. This leads to the exception_handler catching the
            # exception, and if we're lucky users reporting it to our issue
            # tracker
            #
            raise

        except ScanMustStopException as wmse:
            error = ('The following error was detected and could not be'
                     ' resolved:\n%s\n')
            om.out.error(error % wmse)

        except Exception as e:
            msg = 'Unhandled exception "%s", traceback:\n%s'

            if hasattr(e, 'original_traceback_string'):
                # pylint: disable=E1101
                traceback_string = e.original_traceback_string
                # pylint: enable=E1101
            else:
                traceback_string = traceback.format_exc()

            om.out.error(msg % (e, traceback_string))
            raise

        finally:
            time_spent = self.status.get_scan_time()

            om.out.information('Scan finished in %s' % time_spent)
            om.out.information('Stopping the core...')

            self.strategy.stop()
            self.scan_end_hook()

            # Make sure this line is the last one. This avoids race conditions
            # https://github.com/andresriancho/w3af/issues/1487
            self.status.scan_finished()

    @property
    def worker_pool(self):
        """
        :return: Simple property that will always return a Pool in running state
        """
        if self._worker_pool is None:
            # Should get here only on the first call to "worker_pool".
            self._worker_pool = Pool(processes=self.WORKER_THREADS,
                                     worker_names='WorkerThread',
                                     max_queued_tasks=self.WORKER_INQUEUE_MAX_SIZE,
                                     maxtasksperchild=self.WORKER_MAX_TASKS)

            msg = 'Created first Worker pool for core (id: %s)'
            om.out.debug(msg % id(self._worker_pool))

            return self._worker_pool

        if not self._worker_pool.is_running():
            old_pool_id = id(self._worker_pool)

            #
            # Clean-up the old worker pool
            #
            # We want to do this only when running on the main thread because
            # a call to terminate_join() from within a thread in the same worker
            # pool will generate a dead-lock:
            #
            #   * terminate_join() is waiting for threads to terminate
            #   * current thread is running terminate_join()
            #
            # Not terminating and joining a worker pool that has been closed will
            # consume some resources and at the end be just a few threads doing
            # nothing, so it is not that bad...
            #
            if is_main_thread():
                self._worker_pool.terminate_join()

            # Create a new one
            self._worker_pool = Pool(processes=self.WORKER_THREADS,
                                     worker_names='WorkerThread',
                                     max_queued_tasks=self.WORKER_INQUEUE_MAX_SIZE,
                                     maxtasksperchild=self.WORKER_MAX_TASKS)

            msg = ('Created a new worker pool for core (id: %s) because the old'
                   ' one was not in running state (id: %s)')
            om.out.debug(msg % (id(self._worker_pool), old_pool_id))

        return self._worker_pool

    def can_cleanup(self):
        return self.status.get_simplified_status() == STOPPED

    def cleanup(self):
        """
        The GTK user interface calls this when a scan has been stopped
        (or ended successfully) and the user wants to start a new scan.
        All data from the kb is deleted.

        :return: None
        """
        # End the ExtendedUrllib (clear the cache and close connections), this
        # is only useful if there was a previous scan and the user is starting
        # a new one.
        #
        # Please note that I'm not putting this end() thing in scan_end_hook
        # because I want to be able to access the History() item even after the
        # scan has finished to give the user access to the HTTP request and
        # response associated with a vulnerability
        self.uri_opener.restart()
        self.uri_opener.set_exploit_mode(False)
    
        # If this is not the first scan, I want to clear the old bug data
        # that might be stored in the exception_handler.
        self.exception_handler.clear()
        
        # Clean all data that is stored in the kb
        try:
            kb.cleanup()
        except DBMSException as e:
            msg = "Exception trying to clean up KB instance during shutdown"
            om.out.error(msg + ": " + e.message)

        # Stop the parser subprocess
        parser_cache.dpc.clear(ignore_errors=True)

        # Remove the xurllib cache, bloom filters, DiskLists, etc.
        #
        # This needs to be done here and not in stop() because we want to keep
        # these files (mostly the HTTP request/response data) for the user to
        # analyze in the GUI after the scan has finished
        remove_temp_dir(ignore_errors=True)

        # Not cleaning the config is a FEATURE, because the user is most likely
        # going to start a new scan to the same target, and he wants the proxy,
        # timeout and other configs to remain configured as he did it the first
        # time.
        # reload(cf)

        # It is also a feature to keep the misc settings from the last run, this
        # means that we don't cleanup the misc settings.

        # Not calling:
        # self.plugins.zero_enabled_plugins()
        # because I want to keep the selected plugins and configurations

    def can_stop(self):
        return self.status.get_simplified_status() in (RUNNING, PAUSED)

    def stop(self):
        """
        This method is called by the user interface layer, when the user
        "clicks" on the stop button.

        :return: None. The stop method can take some seconds to return.
        """
        om.out.debug('The user stopped the core, finishing threads...')

        # First we stop the uri opener, this will perform the following things:
        #   * Set the _user_stopped attribute to True in uri_opener
        #   * Make all following HTTP requests raise ScanMustStopByUserRequest
        #   * No more HTTP requests are sent to the target
        #   * All plugins will raise ScanMustStopByUserRequest
        #   * Consumers start to stop because of these exceptions
        self.uri_opener.stop()

        # Then we stop the threads which move the fuzzable requests around, in
        # some cases this won't be needed because of the effect generated by the
        # ScanMustStopByUserRequest exception, but we better make sure the
        # threads have died.
        if self.strategy is not None:
            self.strategy.stop()

        stop_start_time = time.time()

        # seconds
        wait_max = 10
        loop_delay = 0.5

        for _ in range(int(wait_max/loop_delay)):
            if not self.status.is_running():
                core_stop_time = epoch_to_string(stop_start_time)
                msg = '%s were needed to stop the core.' % core_stop_time
                break
            
            try:
                time.sleep(loop_delay)
            except KeyboardInterrupt:
                msg = 'The user cancelled the cleanup process, forcing exit.'
                break
            
        else:
            msg = 'The core failed to stop in %s seconds, forcing exit.'
            msg %= wait_max
        
        om.out.debug(msg)

        # Finally we terminate and join the worker pool
        self._terminate_worker_pool()
    
    def quit(self):
        """
        The user wants to exit w4af ASAP, so we stop the scan and exit.
        """
        self.stop()
        self.uri_opener.end()

        # Remove the xurllib cache, bloom filters, DiskLists, etc.
        #
        # This needs to be done here and not in stop() because we want to keep
        # these files (mostly the HTTP request/response data) for the user to
        # analyze in the GUI after the scan has finished
        remove_temp_dir(ignore_errors=True)

        # Stop the parser subprocess
        parser_cache.dpc.clear(ignore_errors=True)

    def pause(self, pause_yes_no):
        """
        Pauses/Un-Pauses scan.
        :param pause_yes_no: True if the UI wants to pause the scan.
        """
        self.status.pause(pause_yes_no)
        self.strategy.pause(pause_yes_no)
        self.uri_opener.pause(pause_yes_no)

    def verify_environment(self):
        """
        Checks if all parameters where configured correctly by the user,
        which in this case is a mix of w4af_console, w4af_gui and the real
        (human) user.
        """
        if not self.plugins.initialized:
            msg = ('You must call the plugins.init_plugins() method before'
                   ' calling start().')
            raise BaseFrameworkException(msg)

        if not self.target.has_valid_configuration():
            raise BaseFrameworkException('No target URI configured.')

        if not len(self.plugins.get_enabled_plugins('audit')) \
           and not len(self.plugins.get_enabled_plugins('crawl')) \
           and not len(self.plugins.get_enabled_plugins('infrastructure')) \
           and not len(self.plugins.get_enabled_plugins('grep')):

            msg = 'No audit, grep or crawl plugins configured to run.'
            raise BaseFrameworkException(msg)

    def _terminate_worker_pool(self):
        om.out.debug('Called _terminate_worker_pool()')

        #
        # Adding extra logging to debug issues where the call to terminate_join()
        # takes a lot of time to run
        #
        monkey_patch_debug()

        #
        # The scan has ended, and we've already joined() the consumer threads
        # from strategy (in a nice way, waiting for them to finish before
        # returning from strategy.start call), so this terminate and join call
        # should return really quick
        #
        self.worker_pool.terminate_join()

        # Disable monkey-patching
        remove_monkey_patch_debug()

    def scan_end_hook(self):
        """
        This method is called when the process ends normally or by an error.
        """
        stop_profiling(self)
        parser_cache.dpc.clear(ignore_errors=True)

        try:
            #
            # Close the output manager, this needs to be done BEFORE the end()
            # in uri_opener because some plugins (namely xml_output) use the
            # data from the history in their end() method.
            #
            # Also needs to be done before target.clear() because some plugins
            # need to access the target data stored in cf
            #
            om.out.debug('Calling end_output_plugins()')
            om.manager.end_output_plugins()
        except Exception:
            raise

        finally:
            self._terminate_worker_pool()

            self.exploit_phase_prerequisites()

            # Remove all references to plugins from memory
            self.plugins.zero_enabled_plugins()
            
            # No targets to be scanned
            self.target.clear()

            # Status
            self.status.stop()

        om.out.debug('scan_end_hook() completed')

    def exploit_phase_prerequisites(self):
        """
        This method is just a way to group all the things that we'll need 
        from the core during the exploitation phase. In other words, which
        internal objects do I need alive after a scan?
        """
        om.out.debug('Setting exploit phase prerequisites')

        # We disable raising the exception, so we do this only once and don't
        # affect other parts of the tool such as the exploitation or manual HTTP
        # request sending from the GUI
        #
        # https://github.com/andresriancho/w3af/issues/2704
        # https://github.com/andresriancho/w3af/issues/2711
        self.uri_opener.clear()

        # Disable some internal checks so the exploits can "bend" the matrix
        self.uri_opener.set_exploit_mode(True)

    def _home_directory(self):
        """
        Handle all the work related to creating/managing the home directory.
        :return: None
        """
        home_dir = get_home_dir()

        # Start by trying to create the home directory (linux: /home/user/.w4af/)
        if not create_home_dir():
            print('Failed to create the w4af home directory "%s".' % home_dir)
            sys.exit(-3)            

        # If this fails, maybe it is because the home directory doesn't exist
        # or simply because it ain't writable|readable by this user
        if not verify_dir_has_perm(home_dir, perm=os.W_OK | os.R_OK, levels=1):
            print('Either the w4af home directory "%s" or its contents are not'
                  ' writable or readable. Please set the correct permissions'
                  ' and ownership. This usually happens when running w4af as'
                  ' root using "sudo".' % home_dir)
            sys.exit(-3)

    def _tmp_directory(self):
        """
        Handle the creation of the tmp directory, where a lot of stuff is stored
        Usually it's something like /tmp/w4af/<pid>/
        """
        try:
            create_temp_dir()
        except Exception:
            msg = ('The w4af tmp directory "%s" is not writable. Please set '
                   'the correct permissions and ownership.' % TEMP_DIR)
            print(msg)
            sys.exit(-3)


def handle_threading_error(scans_completed, threading_error):
    """
    Catch threading errors such as "error: can't start new thread"
    and handle them in a specific way
    """
    active_threads = threading.active_count()
    
    def nice_thread_repr(alive_threads):
        repr_alive = [repr(x) for x in alive_threads]
        repr_alive.sort()
        return pprint.pformat(repr_alive)
    
    pprint_threads = nice_thread_repr(threading.enumerate())
    
    msg = ('A "%s" threading error was found.\n'
           ' The current process has a total of %s active threads and has'
           ' completed %s scans. The complete list of threads follows:\n\n%s')
    raise Exception(msg % (threading_error, active_threads,
                           scans_completed, pprint_threads))
