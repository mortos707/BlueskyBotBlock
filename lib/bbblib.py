import os, sys

# --------------------------------------------------------------------
#
# genReturnDict
#
# --------------------------------------------------------------------
def genReturnDict(msg = "") -> dict:
    """
    This sets up a dictonary that is intented to be returned from
    a function call. The real value here is that this dictonary
    contains information, like the function name and line number,
    about the function. This is handy when debugging a mis-behaving
    function.

    Args:
        msg: A text string containg a simple, short message

    Returns:
        rDict: a dictonary that is returned from a function call

    """
    RS = ReturnStatus()

    rDict = {}

    # These values come from the previous stack frame ie. the
    # calling function.
    rDict['line_number']   = sys._getframe(1).f_lineno
    rDict['filename']      = sys._getframe(1).f_code.co_filename
    rDict['function_name'] = sys._getframe(1).f_code.co_name

    rDict['status']   = RS.OK # See the class ReturnStatus
    rDict['msg']      = msg   # The passed in string
    rDict['data']     = ''    # The data/json returned from func call
    rDict['path']     = ''    # FQPath to file created by func (optional)
    rDict['resource'] = ''    # What resource is being used (optional)

    return rDict
    # End of genReturnDict


# --------------------------------------------------------------------
#
# class ReturnStatus
#
# --------------------------------------------------------------------
class ReturnStatus:
    """
    Since we can't have nice things, like #define, this is
    a stand in.

    These values are intended to be returned from a function
    call. For example

    def bar():
        RS = ReturnStatus()
        rDict = genReturnDict('Demo program bar')

        i = 1 + 1

        if i == 2:
            rDict['status'] = RS.OK
        else:
            rDict['status'] = RS.NOT_OK
            rDict['msg'] = 'Basic math is broken'

        return rDict

    def foo():
        RS = ReturnStatus()

        rDict = bar()
        if rDict['status'] = RS.OK:
            print('All is right with the world')
        else:
            print('We're doomed!')
            print(rDict['msg'])
            sys.exit(RS.NOT_OK)

        return RS.OK

    """

    OK         = 0  # It all worked out
    NOT_OK     = 1  # Not so much
    SKIP       = 2  # We are skipping this block/func
    NOT_YET    = 3  # This block/func is not ready
    FAIL       = 4  # It all went to hell in a handbasket
    NOT_FOUND  = 5  # Could not find what we were looking for
    FOUND      = 6  # Found my keys
    YES        = 7  # Cant believe I missed these
    NO         = 8  #
    RESTRICTED = 9  #
    YES_TO_ALL = 10 #
    # End of class ReturnStatus
