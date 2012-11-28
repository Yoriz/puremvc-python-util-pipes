'''
Created on 26 Nov 2012

@author: Dave Wilson
'''
from puremvc.utilities.pipes import interfaces


class Message(interfaces.IPipeMessage):
    """
    Pipe Message.

    Messages travelling through a Pipeline can be filtered, and queued.
    In a queue, they may be sorted by priority. Based on type, they may used
    as control messages to modify the behaviour of filter or queue fittings
    connected to the pipeline into which they are written.
    """

    PRIORITY_HIGH = 1
    """High priority Messages can be sorted to the front of the queue"""

    PRIORITY_MED = 5
    """Medium priority Messages are the default"""

    PRIORITY_LOW = 10
    """Low priority Messages can be sorted to the back of the queue"""

    BASE = 'http://puremvc.org/namespaces/pipes/messages/'
    NORMAL = BASE + 'normal/'
    """Normal Message type."""

    def __init__(self, msg_type, header=None, body=None, priority=5):
        """
        @param msg_type: Messages can be handled differently according to type
        @param header: Header properties describe any meta data about the
                       message for the recipient
        @param body: Body of the message is the precious cargo
        @param priority: Messages in a queue can be sorted by priority.
        """

        self.msg_type = msg_type
        self.header = header
        self.body = body
        self.priority = priority

    def getType(self):
        """Get the type of this message"""
        return self.msg_type

    def setType(self, msg_type):
        """Set the type of this message"""
        self.msg_type = msg_type

    def getPriority(self):
        """Get the priority of this message"""
        return self.priority

    def setPriority(self, priority):
        """Set the priority of this message"""
        self.priority = priority

    def getHeader(self):
        """Get the header of this message"""
        return self.header

    def setHeader(self, header):
        """Set the header of this message"""
        self.header = header

    def getBody(self):
        """Get the body of this message"""
        return self.body

    def setBody(self, body):
        """Set the body of this message"""
        self.body = body


class FilterControlMessage(Message):
    """
    Filter Control Message.

    A special message type for controlling the behaviour of a Filter.

    The FilterControlMessage.SET_PARAMS message type tells the Filter to
    retrieve the filter parameters object.

    The FilterControlMessage.SET_FILTER message type tells the Filter to
    retrieve the filter function.

    The FilterControlMessage.BYPASS message type tells the Filter that it
    should go into Bypass mode operation, passing all normal messages
    through unfiltered.

    The FilterControlMessage.FILTER message type tells the Filter that it
    should go into Filtering mode operation, filtering all normal normal
    messages before writing out. This is the default mode of operation and so
    this message type need only be sent to cancel a previous
    FilterControlMessage.BYPASS message.

    The Filter only acts on a control message if it is targeted to this named
    filter instance. Otherwise it writes the message through to its output
    unchanged.
    """

    BASE = Message.BASE + 'filter-control/'
    """Message type base URI"""

    SET_PARAMS = BASE + 'setparams'
    """Set filter parameters."""

    SET_FILTER = BASE + 'setfilter'
    """Set filter function."""

    BYPASS = BASE + 'bypass'
    """Toggle to filter bypass mode."""

    FILTER = BASE + 'filter'
    """Toggle to filtering mode. (default behaviour)."""

    def __init__(self, msg_type, name, msg_filter=None, params=None):
        """
        @param name: The target filter name.
        @param msg_filter: The filter function.
        @param params: The parameters object.
        """

        super(FilterControlMessage, self).__init__(msg_type)
        self.name = name
        self.msg_filter = msg_filter
        self.params = params

    def setName(self, name):
        """Set the target filter name."""
        self.name = name

    def getName(self):
        """Get the target filter name."""
        return self.name

    def setFilter(self, msg_filter):
        """Set the filter function."""
        self.msg_filter = msg_filter

    def getFilter(self):
        """Get the filter function."""
        return self.msg_filter

    def setParams(self, params):
        """Set the parameters object."""
        self.params = params

    def getParams(self):
        """Get the parameters object."""
        return self.params


class QueueControlMessage(Message):
    """
    Queue Control Message.

    A special message for controlling the behaviour of a Queue.

    When written to a pipeline containing a Queue, the type of the message is
    interpreted and acted upon by the Queue.

    Unlike filters, multiple serially connected queues aren't very useful and
    so they do not require a name. If multiple queues are connected serially,
    the message will be acted upon by the first queue only.
    """

    BASE = Message.BASE + '/queue/'

    FLUSH = BASE + 'flush'
    """Flush the queue."""

    SORT = BASE + 'sort'
    """Toggle to sort-by-priority operation mode."""

    FIFO = BASE + 'fifo'
    """Toggle to FIFO operation mode (default behaviour)."""

    def __init__(self, msg_type):
        super(QueueControlMessage, self).__init__(msg_type)
