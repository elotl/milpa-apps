import json
# given a response from milpactl
# determine what type it is
# then unserialize into the correct structure

def to_types(struct):
    kind = struct['kind']
    if kind.endswith('List'):
        return to_list(struct)
    else:
        if kind == 'Pod':
            return struct
        elif kind == 'Deployment':
            return struct
        elif kind == 'ReplicaSet':
            return struct
        elif kind == 'Service':
            return struct
        elif kind == 'Node':
            return struct
        elif kind == 'Usage':
            return struct
        else:
            raise Exception(
                "Asked to unserialize unknown object " + kind)


def to_list(liststruct):
    items = liststruct['items']
    return [to_types(item) for item in items]
