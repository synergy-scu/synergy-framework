from uuid import uuid4 as uuidv4

from ..database import connectDB, closeDB
from .channels import get_channels
from ...api.utils.reporter import isError, reportError
from ..utils import listify


def get_device(payload, isGroupQuery = False, groupChannels = []):
    conn, cursor = connectDB()

    try:
        query = ''' SELECT * FROM devices WHERE deviceID = '%s' ''' % (
            payload['deviceID'])
        cursor.execute(query)
        devices = cursor.fetchall()

        if len(devices) > 0:
            # Device IDs should be unique so len(devices) === 1
            device = devices[0]

            if not isGroupQuery:
                return device

            try:
                channels = get_channels(payload, True)

                if isError(channels):
                    responseError = reportError(
                        'An error occured getting the channels for the device with the spcified ID: {}'.format(payload['deviceID']), None)
                    closeDB(conn, cursor)
                    return channels

                if len(channels) == 0:
                    responseError = reportError('CRITICAL ERROR: No channels found for the device with the spcified ID: {}'.format(payload['deviceID']), None)
                    closeDB(conn, cursor)
                    return responseError

                groupChannels.extend(channels)
                result = {
                    'deviceID': device['deviceID'],
                    'name': device['name'],
                    'channels': channels,
                }
                return result

            except Exception as error:
                responseError = reportError('Unable to get channels for the device with the specified ID: {}'.format(payload['deviceID']), error)
                closeDB(conn, cursor)
                return responseError

        else:
            responseError = reportError('No device was found with the specified ID: {}'.format(payload['deviceID']), None)
            closeDB(conn, cursor)
            return responseError
    
    except Exception as error:
        responseError = reportError(
            'SQL ERROR: An error occured getting the device with the specified ID: {}'.format(payload['deviceID']), error)
        closeDB(conn, cursor)
        return responseError

    responseError = reportError(
        'An error occured getting the device with the specified ID: {}'.format(payload['deviceID']), None)
    closeDB(conn, cursor)
    return responseError


def update_device(payload):
    conn, cursor = connectDB()

    try:
        query = ''' UPDATE devices SET name = '%s' WHERE deviceID = '%s' ''' % (
            payload['name'], payload['deviceID'])
        cursor.execute(query)
        closeDB(conn, cursor)
        return payload

    except Exception as error:
        responseError = reportError(
            'SQL ERROR: An error occured updating the name of the channel with the specified ID: {}'.format(payload['channelID']), error)
        closeDB(conn, cursor)
        return responseError

    responseError = reportError(
        'An error occured updating the name of the channel with the specified ID: {}'.format(payload['channelID']), None)
    closeDB(conn, cursor)
    return responseError

def multiplex_devices(payload):
    conn, cursor = connectDB()

    try:
        query = ''' SELECT deviceID FROM devices ORDER BY deviceID ASC LIMIT %s, %s''' % (
            payload['offset'], payload['count'])
        
        cursor.execute(query)
        deviceIDs = cursor.fetchall()
        closeDB(conn, cursor)

        try:

            result = []
            errors = []

            for deviceID in deviceIDs:
                device = get_device(deviceID)
                if isError(device):
                    errors.append(device)
                else:
                    result.append(device)

            if len(errors) > 0:
                return {
                    'error': True,
                    'errors': errors,
                }

            return result

        except Exception as error:
            responseError = reportError(
                'SQL ERROR: An error occurred while retrieving devices', error)
            closeDB(conn, cursor)
            return responseError

    except Exception as error:
        responseError = reportError(
            'An error occurred while retrieving devices', error)
        closeDB(conn, cursor)
        return responseError

    responseError = reportError(
        'An error occurred retrieving devices', None)
    closeDB(conn, cursor)
    return responseError
