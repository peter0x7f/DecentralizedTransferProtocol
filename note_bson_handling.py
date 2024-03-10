import bson

def serialize_data(data):
    """Serializes Python data to BSON format."""
    return bson.dumps(data)

def deserialize_data(bson_data):
    """Deserializes BSON data to Python format."""
    return bson.loads(bson_data)
