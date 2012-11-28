'''
Created on 26 Nov 2012

@author: Dave Wilson
'''
from operator import attrgetter
from puremvc.utilities.pipes import interfaces
from puremvc.utilities.pipes import messages as msgs
from puremvc.patterns import mediator


class Pipe(interfaces.IPipeFitting):
    """
    Pipe.

    This is the most basic IPipeFitting, simply allowing the connection of an
    output fitting and writing of a message to that output.
    """

    def __init__(self, output):
        self.output = output

    def connect(self, output):
        """
        Connect another PipeFitting to the output.

        PipeFittings connect to and write to other PipeFittings in a one-way,
        synchronous chain.

        @return Boolean true if no other fitting was already connected.
        """
        success = False
        if not self.output:
            self.output = output
            success = True

        return success

    def disconnect(self):
        """
        Disconnect the Pipe Fitting connected to the output.

        This disconnects the output fitting, returning a reference to it.
        If you were splicing another fitting into a pipeline, you need to
        keep (at least briefly) a reference to both sides of the pipeline in
        order to connect them to the input and output of whatever fitting that
        you're splicing in.

        @return IPipeFitting the now disconnected output fitting
        """

        disconnectedFitting = self.output
        self.output = None
        return disconnectedFitting

    def write(self, message):
        """
        Write the message to the connected output.

         @param message the message to write
         @return Boolean whether any connected downpipe outputs failed
        """

        return self.output.write(message)


class Filter(Pipe):
    """
    Pipe Filter.

    Filters may modify the contents of messages before writing them to their
    output pipe fitting. They may also have their parameters and filter
    function passed to them by control message, as well as having their
    Bypass/Filter operation mode toggled via control message.
    """

    def __init__(self, name, output=None, msg_filter=None, params=None):
        """Optionally connect the output and set the parameters."""
        super(Filter, self).__init__(output)
        self.name = name
        self.msg_filter = msg_filter
        self.params = params
        self.mode = msgs.FilterControlMessage.FILTER

    def write(self, message):
        """
        Handle the incoming message.

        If message type is normal, filter the message (unless in BYPASS mode)
        and write the result to the output pipe fitting if the filter
        operation is successful.

        The FilterControlMessage.SET_PARAMS message type tells the Filter that
        the message class is FilterControlMessage, which it casts the message
        to in order to retrieve the filter parameters object if the message is
        addressed to this filter.

        The FilterControlMessage.SET_FILTER message type tells the Filter
        that the message class is FilterControlMessage, which it casts the
        message to in order to retrieve the filter function.

        The FilterControlMessage.BYPASS message type tells the Filter that it
        should go into Bypass mode operation, passing all normal messages
        through unfiltered.

        The FilterControlMessage.FILTER message type tells the Filter that it
        should go into Filtering mode operation, filtering all normal normal
        messages before writing out. This is the default mode of operation and
        so this message type need only be sent to cancel a previous BYPASS
        message.

        The Filter only acts on the control message if it is targeted to this
        named filter instance. Otherwise it writes through to the output.

        @return Boolean True if the filter process does not throw an error and
        subsequent operations in the pipeline succeed.
        """

        success = True
        msg_type = message.getType()
        if msg_type == msgs.Message.NORMAL:
            """Filter normal messages"""
            try:
                if self.mode == msgs.FilterControlMessage.FILTER:
                    outputMessage = self.applyFilter(message)
                else:
                    outputMessage = message
                success = self.output.write(outputMessage)
            except Exception as exception:
                success = False
                print "Filter>write eception: %s" % exception

        elif msg_type == msgs.FilterControlMessage.SET_PARAMS:
            """Accept parameters from control message"""
            if self.isTarget(message):
                self.setParams(msgs.FilterControlMessage(message).getParams())
            else:
                success = self.output.write(outputMessage)

        elif msg_type == msgs.FilterControlMessage.SET_FILTER:
            """Accept filter function from control message"""
            if self.isTarget(message):
                self.setParams(msgs.FilterControlMessage(message).getFilter())
            else:
                success = self.output.write(outputMessage)

        elif msg_type == msgs.FilterControlMessage.BYPASS or\
                                msg_type == msgs.FilterControlMessage.FILTER:
            """Toggle between Filter or Bypass operational modes"""

            if self.isTarget(message):
                self.mode = msgs.FilterControlMessage(message).getType()
            else:
                success = self.output.write(outputMessage)

        else:
            """Write control messages for other fittings through"""
            success = self.output.write(outputMessage)

        return success

    def isTarget(self, msg):
        """Is the message directed at this filter instance?"""
        return msgs.FilterControlMessage(msg).getName() == self.name

    def setParams(self, params):
        """
        Set the Filter parameters.

        This can be an object can contain whatever arbitrary properties and
        values your filter method requires to operate.

        @param params the parameters object
        """

        self.params = params

    def setFilter(self, msg_filter):
        """
        Set the Filter function.

        It must accept two arguments; an IPipeMessage, and a parameter Object,
        which can contain whatever arbitrary properties and values your filter
        method requires.

        @param filter the filter function.
        """

        self.msg_filter = msg_filter

    def applyFilter(self, message):
        """Filter the message."""
        self.msg_filter(message, self.params)


class PipeListener(interfaces.IPipeFitting):
    """
    Pipe Listener.

    Allows a class that does not implement IPipeFitting to be the final
    recipient of the messages in a pipeline.

    @see Junction
    """

    def __init__(self, context, listener):
        self.context = context
        self.listener = listener

    def connect(self, output):
        """Can't connect anything beyond this."""
        return False

    def disconnect(self):
        """Can't disconnect since you can't connect, either."""
        return None

    def write(self, message):
        """Write the message to the listener"""
        getattr(self.context, self.listener)(message)


class Junction(object):
    """
    Pipe Junction.

    Manages Pipes for a Module.

    When you register a Pipe with a Junction, it is declared as being an
    INPUT pipe or an OUTPUT pipe.

    You can retrieve or remove a registered Pipe by name, check to see if a
    Pipe with a given name exists,or if it exists AND is an INPUT or an
    OUTPUT Pipe.

    You can send an IPipeMessage on a named INPUT Pipe or add a PipeListener
    to registered INPUT Pipe.
    """

    INPUT = 'input'
    """INPUT Pipe Type"""

    OUTPUT = 'output'
    """OUTPUT Pipe Type"""

    def __init__(self):

        self.inputPipes = set()
        """The names of the INPUT pipes"""

        self.outputPipes = set()
        """The names of the OUTPUT pipes"""

        self.pipesMap = {}
        """The map of pipe names to their pipes"""

        self.pipeTypesMap = {}
        """The map of pipe names to their types"""

    def registerPipe(self, name, pipe_type, pipe):
        """
        Register a pipe with the junction.

        Pipes are registered by unique name and type, which must be either
        Junction.INPUT or Junction.OUTPUT.

        NOTE: You cannot have an INPUT pipe and an OUTPUT pipe registered with
        the same name. All pipe names must be unique regardless of type.

        @return Boolean true if successfully registered. false if another pipe
        exists by that name.
        """

        success = True
        if not self.pipesMap.get(name, None):
            self.pipesMap[name] = pipe
            self.pipeTypesMap[name] = pipe_type
            if pipe_type == Junction.INPUT:
                self.inputPipes.add(name)
            elif pipe_type == Junction.OUTPUT:
                self.outputPipes.add(name)
            else:
                success = False
        else:
            success = False
        return success

    def hasPipe(self, name):
        """
        Does this junction have a pipe by this name?

        @param name the pipe to check for
        @return Boolean whether as pipe is registered with that name.
        """

        return bool(self.pipesMap.get(name, False))

    def hasInputPipe(self, name):
        """
        Does this junction have an INPUT pipe by this name?

        @param name the pipe to check for
        @return Boolean whether an INPUT pipe is registered with that name.
        """

        return self.hasPipe(name) & self.pipeTypesMap[name] == Junction.INPUT

    def hasOutputPipe(self, name):
        """
        Does this junction have an OUTPUT pipe by this name?

        @param name the pipe to check for
        @return Boolean whether an OUTPUT pipe is registered with that name.
        """

        return self.hasPipe(name) & self.pipeTypesMap[name] == Junction.OUTPUT

    def removePipe(self, name):
        """
        Remove the pipe with this name if it is registered.

         NOTE: You cannot have an INPUT pipe and an OUTPUT pipe registered
         with the same name. All pipe names must be unique regardless of type.

         @param name the pipe to remove
        """

        if self.hasPipe(name):
            pipe_type = self.pipeTypesMap[name]
            if pipe_type == Junction.INPUT:
                self.inputPipes.discard(name)

            elif pipe_type == Junction.OUTPUT:
                self.outputPipes.discard(name)

            del self.pipesMap[name]
            del self.pipeTypesMap[name]

    def retrievePipe(self, name):
        """
        Retrieve the named pipe.

        @param name the pipe to retrieve
        @return IPipeFitting the pipe registered by the given name if it exists
        """

        return self.pipesMap.get(name, None)

    def addPipeListener(self, inputPipeName, context, listener):
        """
        Add a PipeListener to an INPUT pipe.

        NOTE: there can only be one PipeListener per pipe, and the listener
        function must accept an IPipeMessage as its sole argument.

        @param name the INPUT pipe to add a PipeListener to
        @param context the calling context or 'this' object
        @param listener the function on the context to call
        """

        success = False
        if self.hasPipe(inputPipeName):
            pipe = self.pipesMap[inputPipeName]
            success = pipe.connect(PipeListener(context, listener))

        return success

    def sendMessage(self, outputPipeName, message):
        """
        Send a message on an OUTPUT pipe.

        @param name the OUTPUT pipe to send the message on
        @param message the IPipeMessage to send
        """

        success = False
        if self.hasPipe(outputPipeName):
            pipe = self.pipesMap[outputPipeName]
            success = pipe.write(message)

        return success


class JunctionMediator(mediator.Mediator):
    """
    Junction Mediator.

    A base class for handling the Pipe Junction in an IPipeAware Core.
    """

    ACCEPT_INPUT_PIPE = 'acceptInputPipe'
    """Accept input pipe notification name constant."""

    ACCEPT_OUTPUT_PIPE = 'acceptOutputPipe'
    """Accept output pipe notification name constant."""

    def __init__(self, name, viewComponent):
        super(JunctionMediator, self).__init__(name, viewComponent)
        self.junction = viewComponent

    def listNotificationInterests(self):
        """
        List Notification Interests.

        Returns the notification interests for this base class.
        Override in subclass and call <code>super.listNotificationInterests
        to get this list, then add any sublcass interests to the array before
        returning.
        """

        return [JunctionMediator.ACCEPT_INPUT_PIPE,
                JunctionMediator.ACCEPT_OUTPUT_PIPE]

    def handleNotification(self, note):
        """
        Handle Notification.

        This provides the handling for common junction activities. It accepts
        input and output pipes in response to IPipeAware interface calls.

        Override in subclass, and call super.handleNotification
        if none of the subclass-specific notification names are matched.
        """

        name = note.getName()
        if name == JunctionMediator.ACCEPT_INPUT_PIPE:
            """
            accept an input pipe
            register the pipe and if successful
            set this mediator as its listener
            """

            inputPipeName = note.getType()
            inputPipe = note.getBody()
            if self.junction.registerPipe(inputPipeName, Junction.INPUT,
                                          inputPipe):
                self.junction.addPipeListener(inputPipeName, self,
                                         self.handlePipeMessage)

        elif name == JunctionMediator.ACCEPT_OUTPUT_PIPE:
            """accept an output pipe"""

            outputPipeName = note.getType()
            outputPipe = note.getBody()
            self.junction.registerPipe(outputPipeName, Junction.OUTPUT,
                                       outputPipe)

    def handlePipeMessage(self, message):
        """
        Handle incoming pipe messages.

        Override in subclass and handle messages appropriately for the module.
        """
        pass


class Queue(Pipe):
    """
    Pipe Queue.

    The Queue always stores inbound messages until you send it a FLUSH control
    message, at which point it writes its buffer to the output pipe fitting.
    The Queue can be sent a SORT control message to go into sort-by-priority
    mode or a FIFO control message to cancel sort mode and return the
    default mode of operation, FIFO.

    NOTE: There can effectively be only one Queue on a given pipeline, since
    the first Queue acts on any queue control message. Multiple queues in one
    pipeline are of dubious use, and so having to name them would make their
    operation more complex than need be.
    """

    def __init__(self, output=None):
        super(Queue, self).__init__(output)
        self.mode = msgs.QueueControlMessage.SORT
        self.messages = []

    def write(self, message):
        """
        Handle the incoming message.

        Normal messages are enqueued.

        The FLUSH message type tells the Queue to write all stored messages
        to the output PipeFitting, then return to normal enqueing operation.

        The SORT message type tells the Queue to sort all subsequent incoming
        messages by priority. If there are unflushed messages in the queue,
        they will not be sorted unless a new message is sent before the next
        FLUSH.
        Sorting-by-priority behaviour continues even after a FLUSH, and can be
        turned off by sending a FIFO message, which is the default behavior
        for enqueue/dequeue.
        """

        success = True
        msg = message.getType()
        if msg == msgs.Message.NORMAL:
            """Store normal messages"""
            self.store(message)

        elif msg == msgs.Message.NORMAL:
            """Flush the queue"""
            success = self.flush()

        elif msg == msgs.QueueControlMessage.SORT or\
                                        msg == msgs.QueueControlMessage.FIFO:
            """
            Put Queue into Priority Sort or FIFO mode
            Subsequent messages written to the queue will be affected.
            Sorted messages cannot be put back into FIFO order!
            """

            self.mode = message.getType()

        return success

    def store(self, message):
        """
        Store a message.
        @param message the IPipeMessage to enqueue.
        @return int the new count of messages in the queue
        """

        self.messages.append(message)
        if self.mode == msgs.QueueControlMessage.SORT:
            self.messages.sort(key=attrgetter("priority"))

    def flush(self):
        """
        Flush the queue.

        NOTE: This empties the queue.</P>
        @return Boolean true if all messages written successfully.
        """

        success = True
        for message in self.messages:
            if not self.output.write(message):
                success = False

        self.messages = []
        return success


class TeeMerge(Pipe):
    """
    Merging Pipe Tee.

    Writes the messages from multiple input pipelines into
    a single output pipe fitting.
    """

    def __init__(self, input1=None, input2=None):
        """
        Constructor.

        Create the TeeMerge and the two optional constructor inputs.
        This is the most common configuration, though you can connect as many
        inputs as necessary by calling connectInput repeatedly.

        Connect the single output fitting normally by calling the connect
        method, as you would with any other IPipeFitting.
        """

        if input1:
            self.connectInput(input1)
        if input2:
            self.connectInput(input2)

    def connectInput(self, input_):
        """
        Connect an input IPipeFitting.

        NOTE: You can connect as many inputs as you want by calling this
        method repeatedly.

        @param input the IPipeFitting to connect for input.
        """

        return input_.connect(self)


class TeeSplit(interfaces.IPipeFitting):
    """
    Splitting Pipe Tee.

    Writes input messages to multiple output pipe fittings.
    """

    def __init__(self, output1=None, output2=None):
        """
        Constructor.

        Create the TeeSplit and connect the up two optional outputs.
        This is the most common configuration, though you can connect as many
        outputs as necessary by calling connect.
        """

        self.outputs = set()
        if output1:
            self.connectInput(output1)
        if output2:
            self.connectInput(output2)

    def connect(self, output):
        """
        Connect the output IPipeFitting.

        NOTE: You can connect as many outputs as you want by calling this
        method repeatedly.

        @param output the IPipeFitting to connect for output.
        """

        self.outputs.add(output)
        return True

    def disconnect(self):
        """
        Disconnect the most recently connected output fitting. (LIFO)

        To disconnect all outputs, you must call this method repeatedly until
        it returns null.

        @param output the IPipeFitting to connect for output.
        """

        return self.outputs.pop()

    def disconnectFitting(self, target):
        """
        Disconnect a given output fitting.

        If the fitting passed in is connected as an output of this TeeSplit,
        then it is disconnected and the reference returned.

        If the fitting passed in is not connected as an output of this
        TeeSplit, then None is returned.

        @param output the IPipeFitting to connect for output.
        """

        removed = None
        if target in self.outputs:
            self.outputs.discard(target)
            removed = target

        return removed

    def write(self, message):
        """
        Write the message to all connected outputs.

        Returns false if any output returns false, but all outputs are written
        to regardless.
        @param message the message to write
        @return Boolean whether any connected outputs failed
        """

        success = True
        for output in self.outputs:
            if not output.write(message):
                success = False

        return success
