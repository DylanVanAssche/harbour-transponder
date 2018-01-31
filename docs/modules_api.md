# Module API
This document describes the needed methods for every supported module in
Transponder. If you want to add your own provider you need to implement several
methods to connect the UI with your provider his SDK.

Your provider may not support all of these methods, if that's the case these
methods need to return an empty list, string, ... depending on the method.

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
