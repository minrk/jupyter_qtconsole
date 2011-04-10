# System library imports
from IPython.external.qt import QtGui

# Local imports
from console_widget import ConsoleWidget


class HistoryConsoleWidget(ConsoleWidget):
    """ A ConsoleWidget that keeps a history of the commands that have been
        executed and provides a readline-esque interface to this history.
    """
    
    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        super(HistoryConsoleWidget, self).__init__(*args, **kw)

        # HistoryConsoleWidget protected variables.
        self._history = []
        self._history_edits = {}
        self._history_index = 0
        self._history_prefix = ''

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def execute(self, source=None, hidden=False, interactive=False):
        """ Reimplemented to the store history.
        """
        if not hidden:
            history = self.input_buffer if source is None else source

        executed = super(HistoryConsoleWidget, self).execute(
            source, hidden, interactive)

        if executed and not hidden:
            # Save the command unless it was an empty string or was identical 
            # to the previous command.
            history = history.rstrip()
            if history and (not self._history or self._history[-1] != history):
                self._history.append(history)

            # Emulate readline: reset all history edits.
            self._history_edits = {}

            # Move the history index to the most recent item.
            self._history_index = len(self._history)

        return executed

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _up_pressed(self):
        """ Called when the up key is pressed. Returns whether to continue
            processing the event.
        """
        prompt_cursor = self._get_prompt_cursor()
        if self._get_cursor().blockNumber() == prompt_cursor.blockNumber():

            # Set a search prefix based on the cursor position.
            col = self._get_input_buffer_cursor_column()
            input_buffer = self.input_buffer
            if self._history_index == len(self._history) or \
                    (self._history_prefix and col != len(self._history_prefix)):
                self._history_index = len(self._history)
                self._history_prefix = input_buffer[:col]

            # Perform the search.
            self.history_previous(self._history_prefix)

            # Go to the first line of the prompt for seemless history scrolling.
            # Emulate readline: keep the cursor position fixed for a prefix
            # search.
            cursor = self._get_prompt_cursor()
            if self._history_prefix:
                cursor.movePosition(QtGui.QTextCursor.Right, 
                                    n=len(self._history_prefix))
            else:
                cursor.movePosition(QtGui.QTextCursor.EndOfLine)
            self._set_cursor(cursor)

            return False

        return True

    def _down_pressed(self):
        """ Called when the down key is pressed. Returns whether to continue
            processing the event.
        """
        end_cursor = self._get_end_cursor()
        if self._get_cursor().blockNumber() == end_cursor.blockNumber():

            # Perform the search.
            self.history_next(self._history_prefix)

            # Emulate readline: keep the cursor position fixed for a prefix
            # search. (We don't need to move the cursor to the end of the buffer
            # in the other case because this happens automatically when the
            # input buffer is set.)
            if self._history_prefix:
                cursor = self._get_prompt_cursor()
                cursor.movePosition(QtGui.QTextCursor.Right, 
                                    n=len(self._history_prefix))
                self._set_cursor(cursor)

            return False

        return True

    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' public interface
    #---------------------------------------------------------------------------

    def history_previous(self, prefix=''):
        """ If possible, set the input buffer to a previous history item.

        Parameters:
        -----------
        prefix : str, optional
            If specified, search for an item with this prefix.
        """
        index = self._history_index
        while index > 0:
            index -= 1
            history = self._get_edited_history(index)
            if history.startswith(prefix):
                break
        else:
            history = None
        
        if history is not None:
            self._set_edited_input_buffer(history)
            self._history_index = index

    def history_next(self, prefix=''):
        """ If possible, set the input buffer to a subsequent history item.

        Parameters:
        -----------
        prefix : str, optional
            If specified, search for an item with this prefix.
        """
        index = self._history_index
        while self._history_index < len(self._history):
            index += 1
            history = self._get_edited_history(index)
            if history.startswith(prefix):
                break
        else:
            history = None

        if history is not None:
            self._set_edited_input_buffer(history)
            self._history_index = index

    def history_tail(self, n=10):
        """ Get the local history list.

        Parameters:
        -----------
        n : int
            The (maximum) number of history items to get.
        """
        return self._history[-n:]
        
    #---------------------------------------------------------------------------
    # 'HistoryConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _get_edited_history(self, index):
        """ Retrieves a history item, possibly with temporary edits.
        """
        if index in self._history_edits:
            return self._history_edits[index]
        return self._history[index]

    def _set_edited_input_buffer(self, source):
        """ Sets the input buffer to 'source', saving the current input buffer
            as a temporary history edit.
        """
        self._history_edits[self._history_index] = self.input_buffer
        self.input_buffer = source

    def _set_history(self, history):
        """ Replace the current history with a sequence of history items.
        """
        self._history = list(history)
        self._history_edits = {}
        self._history_index = len(self._history)
