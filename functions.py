import math

def dist_vec(vec1, vec2):
    return math.sqrt((vec1.x - vec2.x) ** 2 + (vec1.y - vec2.y) ** 2)


def find_the_closest_object(my_pos, obj_seq):
    dists_dict = {}
    positions = [o.pos for o in obj_seq]
    for i in range(len(obj_seq)):
        dists_dict[obj_seq[i]] = dist_vec(positions[i], my_pos)
    min_dist = min(list(dists_dict.values()))
    closest = None
    for n, v in enumerate(list(dists_dict.values())):
        if math.isclose(v, min_dist):
            closest = list(dists_dict.keys())[n]

    return closest

def translate(val, start_first_range, end_first_range, start_second_range, end_second_range):
    # find length of each range
    first_range_length = end_first_range - start_first_range
    second_range_length = end_second_range - start_second_range

    # how far val is in the first range and how much it is in the second range
    in_second_range = ((val - start_first_range) / first_range_length) * second_range_length

    return start_second_range + in_second_range


