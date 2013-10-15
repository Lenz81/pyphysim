#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Implement classes to represent the progress of a task.

Use the ProgressbarText class for tasks that do not use multiprocessing,
and the ProgressbarMultiProcessText class for tasks using multiprocessing.

Basically, the task code must call the "progress" function to update the
progress bar and pass a number equivalent to the increment in the progress
since the last call. The progressbar must know the maximum value equivalent
to all the progress, which is passed during object creator for
ProgressbarText class.

The ProgressbarMultiProcessText is similar to ProgressbarText class,
accounts for the progress of multiple processes. For each process you need
to call the register_client_and_get_proxy_progressbar to get a proxy
progressbar, where the maximum value equivalent to all the progress that
will be performed by that process is passed in this proxy creation. Each
process then calls the progress method of the proxy progressbar.

Note that there is also a DummyProgressbar whose progress function does
nothing. This is useful when you want to give the user a choice to show or
not the progressbar such that the task code can always call the progress
method and you only change the progressbar object.
"""

from __future__ import print_function

__revision__ = "$Revision$"

import sys
import multiprocessing
import time

try:
    import zmq
except ImportError:  # pragma: no cover
    # We don't have a fallback for zmq, but only the ProgressbarZMQText and
    # ProgressbarZMQProxy classes require it
    pass

__all__ = ['DummyProgressbar', 'ProgressbarText', 'ProgressbarText2', 'ProgressbarText3', 'ProgressbarMultiProcessText', 'ProgressbarZMQText', 'center_message']


def center_message(message, length=50, fill_char=' ', left='', right=''):
    """Return a string with `message` centralized and surrounded by
    `fill_char`.

    Parameters
    ----------
    message: str
        The message to be centered.
    length : int
        Total length of the centered message (original + any fill).
    fill_char : str
        Filling character.
    left : str
        Left part of the filling.
    right : str
       Right part of the filling.

    Returns
    -------
    cent_message : str
        The centralized message.

    Examples
    --------
    >>> print(center_message("Hello World", 50, '-', 'Left', 'Right'))
    Left-------------- Hello World --------------Right
    """
    message_size = len(message)
    left_size = len(left)
    right_size = len(right)
    fill_size = (length - (message_size + 2) - left_size - right_size)
    left_fill_size = fill_size // 2 + (fill_size % 2)
    right_fill_size = (fill_size // 2)

    new_message = "{0}{1} {2} {3}{4}".format(
        left,
        fill_char * left_fill_size,
        message,
        fill_char * right_fill_size,
        right)
    return new_message


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx DummyProgressbar - START xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class DummyProgressbar(object):  # pragma: no cover
    """Dummy progress bar that don't really do anything.

    The idea is that it can be used in place of the
    :class:`ProgressbarText` class, but without actually doing anything.

    See also
    --------
    ProgressbarText
    """

    def __init__(self, ):
        """Initializes the DummyProgressbar object."""
        pass

    def progress(self, count):
        """This `progress` method has the same signature from the one in the
        :class:`ProgressbarText` class.

        Nothing happens when this method is called.

        Parameters
        ----------
        count : int
            Ignored
        """
        pass
# xxxxxxxxxx DummyProgressbar - END xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx ProgressbarText - START xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# http://code.activestate.com/recipes/299207-console-text-progress-indicator-class/
# CLASS NAME: ProgressbarText
#
# Original Author of the ProgressbarText class:
# Larry Bates (lbates@syscononline.com)
# Written: 12/09/2002
#
# Modified by Darlan Cavalcante Moreira in 10/18/2011
# Released under: GNU GENERAL PUBLIC LICENSE
class ProgressbarText(object):
    """Class that prints a representation of the current progress as
    text.

    You can set the final count for the progressbar, the character that
    will be printed to represent progress and a small message indicating
    what the progress is related to.

    In order to use this class, create an object outsize a loop and inside
    the loop call the `progress` function with the number corresponding to
    the progress (between 0 and finalcount). Each time the `progress`
    function is called a number of characters will be printed to show the
    progress. Note that the number of printed characters correspond is
    equivalent to the progress minus what was already printed.

    See also
    --------
    DummyProgressbar

    Examples
    --------
    >> pb = ProgressbarText(100, 'o', "Hello Simulation")
    >> pb.progress(20)
    ---------------- Hello Simulation ---------------1
        1    2    3    4    5    6    7    8    9    0
    ----0----0----0----0----0----0----0----0----0----0
    oooooooooo
    >> pb.progress(40)
    oooooooooo
    >> pb.progress(50)
    ooooo
    >> pb.progress(100)
    ooooooooooooooooooooooooo
    """
    def __init__(self, finalcount, progresschar='*', message='', output=sys.stdout):
        """Initializes the ProgressbarText object.

        Parameters
        ----------
        finalcount : int
            The total amount that corresponds to 100%. Each time the
            progress method is called with a number that number is added
            with the current amount in the progressbar. When the amount
            becomes equal to `finalcount` the bar will be 100% complete.
        progresschar : str, optional (default to '*')
            The character used to represent progress.
        message : str, optional
            A message to be shown in the top of the progressbar.
        output : File like object
            Object with a 'write' method, which controls where the
            progress-bar will be printed. By default sys.stdout is used,
            which means that the progress will be printed in the standard
            output.
        """
        self.finalcount = finalcount
        self.blockcount = 0  # stores how many characters where already
                             # printed in a previous call to the `progress`
                             # function
        self.block = progresschar  # The character printed to indicate progress
        #
        # By default, self._output points to sys.stdout so I can use the
        # write/flush methods to display the progress bar.
        self._output = output

        self._initialized = False
        self._message = message

    def progress(self, count):
        """Updates the progress bar.

        The value of `count` will be added to the current amount and a
        number of characters used to represent progress will be printed.

        Parameters
        ----------
        count : int
            The new amount of progress. The actual percentage of progress
            is equal to count/finalcount.

        """
        if self._initialized is False:
            # # If the final count is zero, don't start the progress gauge
            # if not self.finalcount:
            #     return
            if(len(self._message) != 0):
                bartitle = '{0}\n'.format(center_message(
                    self._message, 50, '-', '', '1'))
            else:
                bartitle = '------------------ % Progress -------------------1\n'

            self._output.write(bartitle)
            self._output.write('    1    2    3    4    5    6    7    8    9    0\n')
            self._output.write('----0----0----0----0----0----0----0----0----0----0\n')

            self._initialized = True

        #
        # Make sure I don't try to go off the end (e.g. >100%)
        #
        count = min(count, self.finalcount)
        #
        # If finalcount is zero, I'm done
        #
        if self.finalcount:
            percentcomplete = int(round(100 * count / self.finalcount))
            if percentcomplete < 1:
                percentcomplete = 1
        else:
            percentcomplete = 100

        # Divide percentcomplete by two, since we use 50 characters for the
        # full bar. Therefore, the blockcount variable will give us how
        # many characters we need to write to represent the correct
        # percentage of completeness.
        blockcount = int(percentcomplete / 2)
        if blockcount > self.blockcount:
            # The self.blockcount stores how many characters where already
            # printed in a previous call to the `progress`
            # function. Therefore, we only need to print the remaining
            # characters until we reach `blockcount`.
            for i in range(self.blockcount, blockcount):  # pylint:disable=W0612
                self._output.write(self.block)
                self._output.flush()
            # Update self.blockcount
            self.blockcount = blockcount

        # If we completed the bar, print a newline
        if percentcomplete == 100:
            self._output.write("\n")
# xxxxxxxxxx ProgressbarText - END xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx ProgressbarText2 - START xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# The original Code is in
# http://nbviewer.ipython.org/url/github.com/ipython/ipython/raw/master/examples/notebooks/Progress%20Bars.ipynb
# but it was modified to make it more similar to the ProgressbarText class
class ProgressbarText2(object):
    def __init__(self, finalcount, progresschar='*', message='', output=sys.stdout):
        """Initializes the ProgressbarText2 object.

        Parameters
        ----------
        finalcount : int
            The total amount that corresponds to 100%. Each time the
            progress method is called with a number that number is added
            with the current amount in the progressbar. When the amount
            becomes equal to `finalcount` the bar will be 100% complete.
        progresschar : str, optional (default to '*')
            The character used to represent progress.
        message : str, optional
            A message to be shown in the top of the progressbar.
        output : File like object
            Object with a 'write' method, which controls where the
            progress-bar will be printed. By default sys.stdout is used,
            which means that the progress will be printed in the standard
            output.
        """
        self.finalcount = finalcount
        self.prog_bar = '[]'
        self.progresschar = progresschar
        self.width = 50
        # By default, self._output points to sys.stdout so I can use the
        # write/flush methods to display the progress bar.
        self._output = output
        self._message = message
        self._update_amount(0)

    def progress(self, count):
        self._update_iteration(count)
        #print('\r', self, end='')
        self._output.write('\r')
        self._output.write(str(self))
        if count == self.finalcount:
            # Print an empty line after the last iteration to be consistent
            # with the ProgressbarText class
            self._output.write("\n")
            #print('\n')
        sys.stdout.flush()

    def _update_iteration(self, elapsed_iter):
        # Note that self._update_amount will change self.prog_bar
        self._update_amount((elapsed_iter / float(self.finalcount)) * 100.0)

        if(len(self._message) != 0):
            self.prog_bar += "  {0}".format(self._message)
        else:
            self.prog_bar += '  %d of %d complete' % (elapsed_iter, self.finalcount)

    def _update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.progresschar * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) // 2) - len(str(percent_done))
        pct_string = '%d%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def __str__(self):
        return str(self.prog_bar)
# xxxxxxxxxx ProgressbarText2 - END xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx ProgressbarText3 - START xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class ProgressbarText3(object):
    def __init__(self, finalcount, progresschar=' ', message='', output=sys.stdout):
        """Initializes the ProgressbarText3 object.

        Parameters
        ----------
        finalcount : int
            The total amount that corresponds to 100%. Each time the
            progress method is called with a number that number is added
            with the current amount in the progressbar. When the amount
            becomes equal to `finalcount` the bar will be 100% complete.
        progresschar : str, optional (default to '*')
            The character used to represent progress.
        message : str, optional
            A message to be shown in the top of the progressbar.
        output : File like object
            Object with a 'write' method, which controls where the
            progress-bar will be printed. By default sys.stdout is used,
            which means that the progress will be printed in the standard
            output.
        """
        self.finalcount = finalcount
        self.prog_bar = ""
        self.progresschar = progresschar
        self.width = 50
        # By default, self._output points to sys.stdout so I can use the
        # write/flush methods to display the progress bar.
        self._output = output
        self._message = message  # THIS WILL BE IGNORED

    def progress(self, count):
        self._update_iteration(count)
        progress_string = center_message(str(self), fill_char=self.progresschar)
        self._output.write('\r')
        self._output.write(progress_string)
        self._output.write('\n')
        #print('\r', progress_string, sep='', end='\n')

    def _update_iteration(self, elapsed_iter):
        full_count = "{0}/{1}".format(elapsed_iter, self.finalcount)

        if len(self._message) != 0:
            self.prog_bar = "{0} {1}".format(self._message, full_count)
        else:
            self.prog_bar = full_count

    def __str__(self):
        return str(self.prog_bar)
# xxxxxxxxxx ProgressbarText3 - END xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx ProgressbarServerBase xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class ProgressbarDistributedBase(object):
    """
    Base class for progressbars for distributed computations.

    In order to track the progress of distributed computations two classes
    are required, one that acts as a central point and is responsible to
    actually show the progress (the server), and other class that acts as a
    proxy (the client) and is responsible to sending the current progress
    to the server. There will be one object of the "server class" and one
    or more objects of the "client class", each one tracking the progress
    of one of the distributed computations.

    This class is a base class for the "server part", while the
    :class:`ProgressbarDistributedProxyBase` class is a base class for the
    "client part".

    For a full implementation, see the :class:`ProgressbarMultiProcessText`
    and :class:`ProgressbarMultiProcessProxy` classes.
    """

    def __init__(self,
                 progresschar='*',
                 message='',
                 sleep_time=1,
                 filename=None):
        """
        Initializes the ProgressbarDistributedBase object.

        Parameters
        ----------
        progresschar : str
            Character used in the progressbar.
        message : str
            Message writen in the progressbar.
        sleep_time : float
            Time between progressbar updates (in seconds).
        filename : str
            If filename is None (default) then progress will be output to
            sys.stdout. If it is not None then the progress will be output
            to a file with name `filename`. This is usually useful for
            debugging and testing purposes.
        """
        # total_final_count will be updated each time the register_*
        # function is called
        self._total_final_count = 0
        self._progresschar = progresschar
        self._message = message

        self._sleep_time = sleep_time
        self._last_id = -1

        self._filename = filename

        self._manager = multiprocessing.Manager()
        self._client_data_list = self._manager.list()  # pylint: disable=E1101

        # Process responsible to update the progressbar. It will be started
        # by the start_updater method and it may be finished anytime by
        # calling the stop_updater function. Also, it is set as a daemon
        # process so that we don't get errors if the program closes before
        # the process updating the progressbar ends (because the user
        # forgot to call the stop_updater method).
        self._update_process = multiprocessing.Process(name="ProgressBarUpdater", target=self._update_progress, args=[self._filename])
        self._update_process.daemon = True

        # The event will be set when the process updating the progressbar
        # is running and unset (clear) when it is stopped.
        self.running = multiprocessing.Event()  # Starts unset. Is is set
                                                # in the _update_progress
                                                # function

        # # Used for time tracking
        # self._tic = multiprocessing.Value('f', 0.0)
        # self._toc = multiprocessing.Value('f', 0.0)

    def _update_client_data_list(self):
        """
        This method process the communication between the client and the
        server.

        It should gather the information sent by the clients (proxy
        progressbars) and update the member variable self._client_data_list
        accordingly, which will then be automatically represented in the
        progressbar.
        """
        # Implement this method in a derived class.
        pass  # pragma: no cover

    def register_client_and_get_proxy_progressbar(self, total_count):
        """
        Register a new "client" for the progressbar and returns a new proxy
        progressbar that the client can use to update its progress by
        calling the `progress` method of this proxy progressbar.

        Parameters
        ----------
        total_count : int
            Total count that will be equivalent to 100% for function.

        Returns
        -------
        obj : Object of a class derived from ProgressbarDistributedProxyBase
            The proxy progressbar.
        """
        # Implement this method in a derived class
        #
        # Note: The first thing the implementation of this method in a
        # derived class must do is call the _register_client method to
        # register the new client and get its client_id, like the example
        # below
        # >>> client_id = self._register_client(total_count)
        #
        # After that the implementation of
        # register_client_and_get_proxy_progressbar can create the
        # corresponding proxy progressbar passing the client_id and any
        # other required data.
        pass  # pragma: no cover

    def _register_client(self, total_count):
        """
        Register a new "client" for the progressbar and return its `client_id`.

        These returned values must be passed to the corresponding proxy
        progressbar.

        Parameters
        ----------
        total_count : int
            Total count that will be equivalent to 100% progress for the
            function.

        Returns
        -------
        (client_id, client_data_list) : tuple
            A tuple with the client_id and the client_data_list. The
            function whose process is tracked by the
            ProgressbarMultiProcessText must update the element
            `client_id` of the list `client_data_list` with the current
            count.
        """
        self._total_final_count += total_count

        # Update the last_id
        self._last_id += 1

        # client_id that will be used by the function
        client_id = self._last_id

        self._client_data_list.append(0)
        return client_id

    # This method will be run in a different process. Because of this the
    # coverage program does not see that this method in run in the test code
    # even though we know it is run (otherwise no output would
    # appear). Therefore, we put the "pragma: no cover" line in it
    def _update_progress(self, filename=None):  # pragma: no cover
        """
        Collects the progress from each registered proxy progressbar and
        updates the actual visible progressbar.

        Parameters
        ----------
        filename : str
            Name of a file where the data will be written to. If this is
            None then all progress will be printed in the standard output
            (defaut)
        """
        if filename is None:
            import sys
            output = sys.stdout
        else:
            output = open(filename, 'w')

        pbar = ProgressbarText(self._total_final_count,
                               self._progresschar,
                               self._message,
                               output=output)
        self.running.set()
        count = 0
        while count < self._total_final_count and self.running.is_set():
            time.sleep(self._sleep_time)
            # Gather information from all client proxybars and update the
            # self._client_data_list member variable
            self._update_client_data_list()

            # Calculates the current total count from the
            # self._client_data_list
            count = sum(self._client_data_list)

            # Represents the current total count in the progressbars
            pbar.progress(count)

        # It may exit the while loop in two situations: if count reached
        # the maximum allowed value, in which case the progressbar is full,
        # or if the self.running event was cleared in another
        # process. Since in the first case the event is still set, we clear
        # it here to have some consistence (a cleared event will always
        # mean that the progressbar is not running).
        self.running.clear()
        # self._toc.value = time.time()

    def start_updater(self):
        """Start the process that updates the progressbar.
        """
        # self._tic.value = time.time()
        if not self.running.is_set():
            self._update_process.start()

    def stop_updater(self, timeout=None):
        """Stop the process updating the progressbar.

        You should always call this function in your main process (the same
        that created the progressbar) after joining all the processes that
        update the progressbar. This guarantees that the progressbar
        updated any pending change and exited clearly.

        """
        self.running.clear()
        # self._toc.value = time.time()
        self._update_process.join(timeout)

    # # TODO: Check if the duration property work correctly
    # @property
    # def duration(self, ):
    #     """Duration of the progress.

    #     Returns
    #     -------
    #     toc_minus_tic : float
    #         The duration passed until the progressbar reaches 100%.
    #     """
    #     # The progressbar is still running, calculate the duration since
    #     # the beginning
    #     if self.running.is_set():
    #         toc = time.time()
    #     else:
    #         toc = self._toc.value

    #     return toc - self._tic.value


class ProgressbarDistributedProxyBase(object):
    """
    Proxy progressbar that behaves like a ProgressbarText object, but is
    actually updating a shared (with other clients) progressbar.

    The basic idea is that this proxy progressbar has the "progress" method
    similar to the standard ProgressbarText class. However, when this
    method is called it will update a value that will be read by a "server
    progressbar" object which is responsible to actually show the current
    progress.
    """

    def __init__(self, client_id):
        """
        """
        self.client_id = client_id

    # Implement this method in a derived class
    def progress(self, count):
        """Updates the proxy progress bar.

        Parameters
        ----------
        count : int
            The new amount of progress.

        """
        pass  # pragma: no cover


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx ProgressbarMultiProcessText - START xxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class ProgressbarMultiProcessText(ProgressbarDistributedBase):
    """Class that prints a representation of the current progress of
    multiple process as text.

    While the :class:`ProgressbarText` class only tracks the progress of a
    single process, the :class:`ProgressbarMultiProcessText` class can
    track the joint progress of multiple processes. This may be used, for
    instance, when you parallelize some task using the multiprocessing
    module.

    Using the ProgressbarMultiProcessText class requires a little more work
    than using the ProgressbarText class, as it is described in the
    following:

     1. First you create an object of the ProgressbarMultiProcessText class
        as usual. However, differently from the ProgressbarText class you
        don't pass the `finalcount` value to the progressbar yet.
     2. After that, for each process to be tracked, call the
        :meth:`register_client_and_get_proxy_progressbar` method passing
        the number equivalent to full progress for **that process**. This
        function returns a "proxy progressbar" that behaves like a regular
        ProgressbarText. Pass that proxy progressbar as an argument to that
        process so that it can call its "progress" method. Each process
        that calls the "progress" method of the received proxy progressbar
        will actually update the progress of the main
        ProgressbarMultiProcessText object.
     3. Start all the processes and call the start_updater method of
        ProgressbarMultiProcessText object so that the bar is updated by
        the different processes.
     4. After joining all the process (all work is finished) call the
        stop_updater method of the ProgressbarMultiProcessText object.

    Examples
    --------

    .. code-block:: python

       import multiprocessing
       # Create a ProgressbarMultiProcessText object
       pb = ProgressbarMultiProcessText(message="some message")
       # Creates a proxy progressbar for one process passing the value
       # corresponding to 100% progress for the first process
       proxybar1 = pb.register_client_and_get_proxy_progressbar(60)
       # Creates a proxy progressbar for another process
       proxybar2 = pb.register_client_and_get_proxy_progressbar(80)
       # Create the first process passing the first proxy progressbar as
       # an argument
       p1 = multiprocessing.Process(target=some_function, args=[proxybar1])
       # Creates another process
       p2 = multiprocessing.Process(target=some_function, args=[proxybar2])
       # Start both processes
       p1.start()
       p2.start()
       # Call the start_updater method of the ProgressbarMultiProcessText
       pb.start_updater()
       # Joint the process and then call the stop_updater method of the
       # ProgressbarMultiProcessText
       p1.join()
       p2.join()
       pb.stop_updater()

    """

    def __init__(self,
                 progresschar='*',
                 message='',
                 sleep_time=1,
                 filename=None):
        """
        Initializes the ProgressbarMultiProcessText object.

        Parameters
        ----------
        progresschar : str
            Character used in the progressbar.
        message : str
            Message writen in the progressbar.
        sleep_time : float
            Time between progressbar updates (in seconds).
        filename : str
            If filename is None (default) then progress will be output to
            sys.stdout. If it is not None then the progress will be output
            to a file with name `filename`. This is usually useful for
            debugging and testing purposes.
        """
        ProgressbarDistributedBase.__init__(self,
                                            progresschar, message, sleep_time, filename)

    def _update_client_data_list(self):
        """
        This method process the communication between the client and the
        server.
        """
        # Note that since the proxybar (ProgressbarMultiProcessProxy class)
        # for multiprocessing will directly modify the
        # self._client_data_list we don't need to implement a
        # _update_client_data_list method here in the
        # ProgressbarMultiProcessText class.
        pass  # pragma: no cover

    def register_client_and_get_proxy_progressbar(self, total_count):
        """
        Register a new "client" for the progressbar and returns a new proxy
        progressbar that the client can use to update its progress by
        calling the `progress` method of this proxy progressbar.

        The function whose process is tracked by the
        ProgressbarMultiProcessText must must call the `progress` method of
        the returned ProgressbarMultiProcessProxy object with the current
        count. This is a little less intrusive regarding the tracked
        function.

        Parameters
        ----------
        total_count : int
            Total count that will be equivalent to 100% for function.

        Returns
        -------
        obj : ProgressbarMultiProcessProxy object
            The proxy progressbar.
        """
        client_id = self._register_client(total_count)
        return ProgressbarMultiProcessProxy(client_id, self._client_data_list)


# Used by the ProgressbarMultiProcessText class
class ProgressbarMultiProcessProxy(ProgressbarDistributedProxyBase):
    """
    Proxy progressbar that behaves like a ProgressbarText object,
    but is actually updating a ProgressbarMultiProcessText progressbar.

    The basic idea is that this proxy progressbar has the "progress" method
    similar to the standard ProgressbarText class. However, when this
    method is called it will update a value that will be read by a
    ProgressbarMultiProcessText object instead.
    """
    def __init__(self, client_id, client_data_list):
        """Initializes the ProgressbarMultiProcessProxy object."""
        ProgressbarDistributedProxyBase.__init__(self, client_id)
        self._client_data_list = client_data_list

    def progress(self, count):
        """Updates the proxy progress bar.

        Parameters
        ----------
        count : int
            The new amount of progress.

        """
        self._client_data_list[self.client_id] = count
# xxxxxxxxxx ProgressbarMultiProcessText - END xxxxxxxxxxxxxxxxxxxxxxxxxxxx


# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxx ProgressbarZMQText xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
class ProgressbarZMQText2(ProgressbarDistributedBase):
    """
    Distributed "server" progressbar using ZMQ sockets.

    In order to track the progress of distributed computations two classes
    are required, one that acts as a central point and is responsible to
    actually show the progress (the server), and other class that acts as a
    proxy (the client) and is responsible to sending the current progress
    to the server. There will be one object of the "server class" and one
    or more objects of the "client class", each one tracking the progress
    of one of the distributed computations.

    This class acts like the server. It creates a ZMQ socket which expects
    (string) messages in the form "client_id:current_progress", where the
    client_id is the ID of one client progressbar previously registered
    with the register_client_and_get_proxy_progressbar method while the
    current_progress is a "number" with the current progress of that
    client.

    Note that the client proxybar for this class is implemented in the
    ProgressbarZMQProxy class.

    Parameters
    ----------
    progresschar : str
        Character used in the progressbar.
    message : str
        Message writen in the progressbar.
    sleep_time : float
        Time between progressbar updates (in seconds).
    filename : str
        If filename is None (default) then progress will be output to
        sys.stdout. If it is not None then the progress will be output to a
        file with name `filename`. This is usually useful for debugging and
        testing purposes.
    ip : string
        An string representing the address of the server socket.
        Ex: '192.168.0.117', 'localhost', etc.
    port : int
        The port to bind the socket.
    """

    def __init__(self,
                 progresschar='*',
                 message='',
                 sleep_time=1,
                 filename=None,
                 ip='localhost',
                 port=7396):
        """
        Initializes the ProgressbarDistributedBase object.

        Parameters
        ----------
        progresschar : str
            Character used in the progressbar.
        message : str
            Message writen in the progressbar.
        sleep_time : float
            Time between progressbar updates (in seconds).
        filename : str
            If filename is None (default) then progress will be output to
            sys.stdout. If it is not None then the progress will be output
            to a file with name `filename`. This is usually useful for
            debugging and testing purposes.
        ip : string
            An string representing the address of the server socket.
            Ex: '192.168.0.117', 'localhost', etc.
        port : int
            The port to bind the socket.
        """
        ProgressbarDistributedBase.__init__(self,
                                            progresschar, message, sleep_time, filename)

        # Create a Multiprocessing namespace
        self._ns = self._manager.Namespace()

        # We store the IP and port of the socket in the Namespace, since
        # the socket will be created in a different process
        self._ns.ip = ip
        self._ns.port = port

    def _get_ip(self):
        """Get method for the ip property."""
        return self._ns.ip
    ip = property(_get_ip)

    def _get_port(self):
        """Get method for the port property."""
        return self._ns.port
    port = property(_get_port)

    def register_client_and_get_proxy_progressbar(self, total_count):
        client_id = self._register_client(total_count)
        proxybar = ProgressbarZMQProxy(client_id, self.ip, self.port)
        return proxybar

    def _update_progress(self, filename=None):
        """
        Collects the progress from each registered proxy progressbar and
        updates the actual visible progressbar.

        Parameters
        ----------
        filename : str
            Name of a file where the data will be written to. If this is
            None then all progress will be printed in the standard output
            (defaut)

        Notes
        -----
        We re-implement it here only to create the ZMQ socket. After that we
        call the base class implementation of _update_progress method. Note
        that the _update_progress method in the base class calls the
        _update_client_data_list and we indeed re-implement this method in
        this class and use the socket created here in that implementation.
        """
        # First we create the context and the socket. Then we bind the
        # socket to the respective ip:port.
        self._zmq_context = zmq.Context()
        self._zmq_pull_socket = self._zmq_context.socket(zmq.PULL)
        self._zmq_pull_socket.bind("tcp://*:%s" % self.port)
        ProgressbarDistributedBase._update_progress(self, filename)

    def _update_client_data_list(self):
        """
        This method process the communication between the client and the
        server.

        This method will read the received messages in the socket which
        were sent by the clients (ProgressbarZMQProxy objects) and update
        self._client_data_list variable accordingly. The messages are in
        the form "client_id:current_progress", which is parsed by the
        _parse_progress_message method.

        Notes
        -----
        This method is called inside a loop in the _update_progress method.
        """

        pending_mensages = True
        while pending_mensages is True and self.running.is_set():
            try:
                # Try to read a message. If this fail we will get a
                # zmq.ZMQError exception and then pending_mensages will be
                # set to False so that we exit the while loop.
                message = self._zmq_pull_socket.recv_string(flags=zmq.NOBLOCK)

                # If we are here that means that a new message was
                # successfully received from the client.  Let's call the
                # _parse_progress_message method to parse the message and
                # update the self._client_data_list member variable.
                self._parse_progress_message(message)
            except zmq.ZMQError:
                pending_mensages = False

    def _parse_progress_message(self, message):
        """
        Parse the message sent from the client proxy progressbars.

        The messages sent from the proxy progressbars are in the form
        'client_id:current_count'. We need to set the element of index
        "client_id" in self._client_data_list to the value of
        "current_count". This method will simply parse the message and
        perform this operation.

        Parameters
        ----------
        message : str
            A string in the form 'client_id:current_count'.
        """
        client_id, current_count = map(int, message.split(":"))
        self._client_data_list[client_id] = current_count


class ProgressbarZMQText(object):
    """Progressbar using ZMQ sockets.
    """
    def __init__(self,
                 progresschar='*',
                 message='',
                 sleep_time=2,
                 filename=None):
        """
        Initializes the ProgressbarMultiProcessText object.

        Parameters
        ----------
        progresschar : str
            Character used in the progressbar.
        message : str
            Message writen in the progressbar.
        sleep_time : float
            Time between progressbar updates (in seconds).
        filename : str
            If filename is None (default) then progress will be output to
            sys.stdout. If it is not None then the progress will be output
            to a file with name `filename`. This is usually useful for
            debugging and testing purposes.
        """
        # total_final_count will be updated each time the register_*
        # function is called
        self._total_final_count = 0
        self._progresschar = progresschar
        self._message = message

        self._sleep_time = sleep_time
        self._last_id = -1

        self._filename = filename

        # Each time we register a client we add a value here for that
        # client. When the client updates its value we update the
        # corresponding value here. In order to obtain the total amount
        # already run all we need to do is to is to sum all the values
        # here.
        self._client_data_list = []

        self.running = False

        # xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        # Server information
        self._ip = 'localhost'
        self._port = None

        # Bind the server socket
        self._zmq_context = zmq.Context()
        self._zmq_pull_socket = self._zmq_context.socket(zmq.PULL)
        if self._port is None:
            self._port = self._zmq_pull_socket.bind_to_random_port("tcp://*")
        else:
            self._zmq_pull_socket.bind("tcp://*:%s" % self._port)

    def _register_client(self, total_count):
        """
        Register a new client for the progressbar and return its `client_id` as
        well as the IP and PORT that the client should use to update its
        progress.

        These returned values must be passed to the corresponding proxy
        progressbar.

        Parameters
        ----------
        total_count : int
            Total count that will be equivalent to 100% progress for the
            function.

        Returns
        -------
        (client_id, IP, PORT) : tuple of 3 integers
            A tuple with the client_id, the IP and the PORT that will be
            necessary to create the proxy progressbar (see the
            :class:`ProgressbarZMQProxy` class)
        """
        self._total_final_count += total_count

        # Update the last_id
        self._last_id += 1

        # client_id that will be used by the function
        client_id = self._last_id

        self._client_data_list.append(0)
        return (client_id, self._ip, self._port)

    def register_client_and_get_proxy_progressbar(self, total_count):
        """
        Creates a new proxy progressbar that can be used to update the main
        progressbar.

        The returned progressbar should be passed to the processing that
        wants to update the progress.

        Parameters
        ----------
        total_count : int
            Total count that will be equivalent to 100% for function.

        Returns
        -------
        obj : ProgressbarZMQProxy object
            The proxy progressbar.
        """
        return ProgressbarZMQProxy(*self._register_client(total_count))

    def _parse_progress_message(self, message):
        """
        Parse the message sent from the client proxy progressbars.

        The messages sent from the proxy progressbars are in the form
        'client_id:current_count'. We need to set the element of index
        "client_id" in self._client_data_list to the value of
        "current_count". This method will simply parse the message and
        perform this operation.

        Parameters
        ----------
        message : str
            A string in the form 'client_id:current_count'.
        """
        client_id, current_count = map(int, message.split(":"))
        self._client_data_list[client_id] = current_count

    def start_updater(self):
        """
        Start the updating of the progressbar that updates the progressbar.

        This will create the socket that receives the progress from the
        clients and update the actual progressbar.
        """
        from time import sleep

        if self._filename is None:
            import sys
            output = sys.stdout
        else:
            output = open(filename, 'w')

        pbar = ProgressbarText(self._total_final_count,
                               self._progresschar,
                               self._message,
                               output=output)

        self.running = True
        count = 0
        while count < self._total_final_count and self.running is True:
            try:
                # Try to receive something in the socket.
                message = self._zmq_pull_socket.recv_string(flags=zmq.NOBLOCK)
                # This will update self._client_data_list
                self._parse_progress_message(message)

                count = sum(self._client_data_list)
                pbar.progress(count)
                # and print the received value
            except zmq.ZMQError:
                # If we could not receive anything in the socket it will
                # trown the ZMQError exception. In that case we sleep for
                # "self._sleep_time" seconds.
                sleep(self._sleep_time)

        self.running = False

    def stop_updater(self, timeout=None):
        """Stop the process updating the progressbar.

        You should always call this function in your main process (the same
        that created the progressbar) after joining all the processes that
        update the progressbar. This guarantees that the progressbar
        updated any pending change and exited clearly.

        """
        pass


# Used by the ProgressbarZMQText class
class ProgressbarZMQProxy(object):
    """
    Proxy progressbar that behaves like a ProgressbarText object,
    but is actually updating a ProgressbarZMQText progressbar.

    The basic idea is that this proxy progressbar has the "progress" method
    similar to the standard ProgressbarText class. However, when this
    method is called it will update a value that will be read by a
    ProgressbarZMQText object instead.
    """
    def __init__(self, client_id, ip, port):
        """Initializes the ProgressbarZMQProxy object."""
        # We import zmq here inside the class to avoid the whole module not
        # working if zmq is not available. That means that we will only get
        # the import error when zmq is not available if we actually try to
        # instantiate ProgressbarZMQText.
        self.client_id = client_id
        self.ip = ip
        self.port = port

        # Function that will be called to update the progress. This
        # variable is initially set to the "_connect_and_update_progress"
        # method that will create the socket, connect it to the main
        # progressbar and finally set "_progress_func" to the "_progress"
        # method that will actually update the progress.
        self._progress_func = ProgressbarZMQProxy._connect_and_update_progress

        # ZMQ Variables: These variables will be set the first time the
        # progress method is called.
        self._zmq_context = None
        self._zmq_push_socket = None

    def progress(self, count):
        """Updates the proxy progress bar.

        Parameters
        ----------
        count : int
            The new amount of progress.

        """
        self._progress_func(self, count)

    def __call__(self, count):
        """
        Updates the proxy progress bar.

        This method is the same as the :meth:`progress`. It is define so
        that a ProgressbarZMQProxy object can behave like a function.
        """
        self._progress_func(self, count)

    def _progress(self, count):
        """

        Parameters
        ----------
        count : int
        """
        # The mensage is a string composed of the client ID and the current
        # count
        message = "{0}:{1}".format(self.client_id, count)
        self._zmq_push_socket.send_string(message, flags=zmq.NOBLOCK)

    def _connect_and_update_progress(self, count):
        """
        Creates the "push socket", connects it to the socket of the main
        progressbar and then updates the progress.

        This function will be called only in the first time the "progress"
        method is called. Subsequent calls to "progress" will actually
        calls the "_progress" method.

        Parameters
        ----------
        count : int
            The new amount of progress.
        """
        self._zmq_context = zmq.Context()
        self._zmq_push_socket = self._zmq_context.socket(zmq.PUSH)
        self._zmq_push_socket.connect("tcp://{0}:{1}".format(self.ip, self.port))
        self._progress_func = ProgressbarZMQProxy._progress
        self._progress_func(self, count)
# xxxxxxxxxx ProgressbarZMQText - END xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
