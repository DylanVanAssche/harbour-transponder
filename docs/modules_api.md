# Module API
This document describes the needed methods for every supported module in
Transponder. If you want to add your own provider you need to implement several
methods to connect the UI with your provider his SDK.

Your provider may not support all of these methods, if that's the case these
methods need to return an empty list, string, ... depending on the method.

To make Transponder more modular every provider needs to be implemented as a class called `Client`. The `SDK` class in Transponder will look for this when it's tries to import the provider module.

## get_messages
This method should return a list of `Message` objects containing all the
messages of the supplied `Contact` object.

## get_contacts
This method should return a list of `Contact` objects for your provider.

## login
Authentication with your provider is handled here. The default arguments are:
- username
- password
- host

## logout
Logging out of the provider

## send_message
Sending a message requires 2 things:
- Contact object who will receive the message
- Message object with the message text

# event_listener
A method where all events for your provider will land, currently the following
events are supported:
- New message
- Authentication error
- New invite


:exclamation: This method will not be called directly but needs to receive events from the provider. As soon as an event is received, the event needs to be send to QML using `pyotherside.send(signal, data)`
