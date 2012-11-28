'''
Created on 25 Nov 2012

@author: Dave Wilson
'''


class IPipeFitting(object):
    """
    Pipe Fitting Interface.

    A IPipeFitting can be connected to other IPipeFittings, forming a Pipeline.
    IPipeMessages are written to one end of a Pipeline by some client code.
    The messages are then transfered in synchronous fashion from one fitting
    to the next.
    """
    def connect(self, output):
        """
        Connect another Pipe Fitting to the output.

        Fittings connect and write to other fittings in a one way synchronous
        chain, as water typically flows one direction through a physical pipe.

        @return Boolean true if no other fitting was already connected.
        """
        raise NotImplementedError(self)

    def disconnect(self):
        """
        Disconnect the Pipe Fitting connected to the output.

        This disconnects the output fitting, returning a reference to it.
        If you were splicing another fitting into a pipeline,
        you need to keep (at least briefly) a reference to both sides of the
        pipeline in order to connect them to the input and output of whatever
        fitting that you're splicing in.

        @return IPipeFitting the now disconnected output fitting
        """
        raise NotImplementedError(self)

    def write(self, message):
        """
        Write the message to the output Pipe Fitting.

        There may be subsequent filters and trees
        (which also implement this interface), that the fitting is writing to,
        and so a message may branch and arrive in different forms at
        different end points.

        If any fitting in the chain returns false
        from this method, then the client who originally
        wrote into the pipe can take action, such as
        rolling back changes.
        """
        raise NotImplementedError(self)


class IPipeAware(IPipeFitting):
    """
    Pipe Aware interface.

    Can be implemented by any PureMVC Core that wishes to communicate with
    other Cores using the Pipes utility.
    """

    def acceptInputPipe(self, name, pipe):
        raise NotImplementedError(self)

    def acceptOutputPipe(self, name, pipe):
        raise NotImplementedError(self)


class IPipeMessage(object):
    """
    Pipe Message Interface.

    IPipeMessage are objects written into a Pipeline, composed of
    IPipeFittings. The message is passed from one fitting to the next in
    synchronous fashion.

    Depending on type, messages may be handled differently by the fittings.
    """

    def getType(self):
        """Get the type of this message"""
        raise NotImplementedError(self)

    def setType(self, msg_type):
        """Set the type of this message"""
        raise NotImplementedError(self)

    def getPriority(self):
        """Get the priority of this message"""
        raise NotImplementedError(self)

    def setPriority(self, priority):
        """Set the priority of this message"""
        raise NotImplementedError(self)

    def getHeader(self):
        """Get the header of this message"""
        raise NotImplementedError(self)

    def setHeader(self, header):
        """Set the header of this message"""
        raise NotImplementedError(self)

    def getBody(self):
        """Get the body of this message"""
        raise NotImplementedError(self)

    def setBody(self, body):
        """Set the body of this message"""
        raise NotImplementedError(self)
