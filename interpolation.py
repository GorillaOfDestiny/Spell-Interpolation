
from importlib import resources
import aspects
import numpy as np
import matplotlib.pyplot as plt
import json
import glob
import os
import itertools

POSITIVES = ["Beyond","Heat","Light","Life","Prodigiouss","Energy","Extrospection","Flexibility","Hope","Movement"]
NEGATIVES = ["Within","Cold","Dark","Death","Diminutive","Potential","Introspection","Rigidity","Hopelessness","Stagnency"]

def interpolate(A: np.ndarray, B: np.ndarray, f: float) -> np.ndarray:
    return((1-f)*A + f*B)

def read_json(json_file) -> dict:
    with open(json_file,"r") as f:
        data = json.load(f)
    return(data)

def aspect_to_coords(aspect_str)-> np.ndarray:
    
    coords = np.zeros(len(POSITIVES))
    if aspect_str in POSITIVES:
        coords[POSITIVES.index(aspect_str)] = 1
        return(coords)
    elif aspect_str in NEGATIVES:
        coords[NEGATIVES.index(aspect_str)] = -1
        return(coords)
    elif "Num" in aspect_str or "Dist" in aspect_str or isinstance(aspect_str,list):
        return(coords)
    else:
        raise KeyError(f"{aspect_str} not in {POSITIVES}\n or {NEGATIVES}")

def attribute_to_coords(aspect_list) -> np.ndarray:
    coords = np.zeros(10)
    for aspect_str in aspect_list:
        coords += aspect_to_coords(aspect_str)
    return(coords)

def get_all_attribute_coords(json_file):
    test_json = read_json(json_file)
    att_keys = test_json.keys()
    att_coords = []
    for ak in att_keys:
        att_coords.append(attribute_to_coords(test_json[ak]))
    return att_coords,att_keys

def test_interpolation(coord0, coord1, inter_density = 1000, threshold = 0.25):
    passed_points = []
    err = []
    F = []
    for f in np.linspace(0, 1, inter_density):
        new_point = interpolate(coord0,coord1,f)
        new_point_int = np.round(new_point, 0)
        err_ = np.sum(np.abs(new_point - new_point_int))/10
        if err_ < threshold:
            
            if len(passed_points) > 0:
                if np.min(np.sqrt(np.sum(np.square(new_point_int - np.array(passed_points)),axis = 1))) != 0:
                    passed_points.append(new_point_int)
                    err.append(err_*10)
                    F.append(f)
            else:
                passed_points.append(new_point_int)
                err.append(err_)
                F.append(f)
    return(passed_points[1:-1], err[1:-1], F[1:-1])


def l1_distance(vec1: np.ndarray, vec2: np.ndarray) -> np.float64:
    """Calculates the l1_distance
    
    Parameters
    ----------
    vec1: np.ndarray
        first vector 
    vec2: np.ndarray
        second vector
    
    Returns
    -------
    np.ndarray
        The total l1_distance between the two points
    """
    return np.sum(abs(vec1-vec2))


def simple_search_interpolation(vec1: np.ndarray,
                                vec2: np.ndarray,
                                density: int=1_001,
                                threshold: float=1e-6) -> list[dict]:
    """Alternative search implementation that only looks for candidate points without
    collecting "close enough" points
    
    Parameters
    ----------
    vec1: np.ndarray
        Vector 1 for the interpolation
    vec2: np.ndarray
        Vector 2 for the interpolation
    density: int; default=1001
        The number of interpolation points to search
    threshold: float; default=1e-6
        Numerical percision for the sum of l1-distances to be considered "zero"
        (This is because I'm lazy and don't want to cast my arrays as ints for exact deltas)
    
    Returns
    list[dict]
        List of dictionarys. Dictionaries have the following key value pairs
            - point: The viable new intermediate point
            - interp_frac: The fraction of interpolation between vec1 and vec2 that
                           generates this new point
    """
    viable_points = []
    for f in np.linspace(0, 1, density):
        new_point = interpolate(vec1, vec2, f)
        new_point_int = np.round(new_point, 0)
        
        # Not very interesting if it would round to end points
        if l1_distance(new_point_int, vec1) < threshold:
            continue
        if l1_distance(new_point_int, vec2) < threshold:
            continue
        delta = np.sum(abs(new_point-new_point_int))
        if delta < threshold:
            viable_points.append({'point':new_point,
                                  'interp_frac': f})
    return viable_points

def get_nearest_f(A,B,interp_point):
    # Mostly based on https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
    # section "Vector Formulation"
    
    #get normal vector, n
    n = B - A
    n = n/np.linalg.norm(n)
    
    #get difference between initial point and interpolation point
    # this is a vector from P to A
    diff = (A - interp_point)

    #get distance between the nearest point on line AB to P, and A
    # np.dot(diff,n) is the projection of thje line PA to the line AB
    # multiply by the normal vector "n" to turn this into a vector so that 
    # (diff.n)*n is the lenth on the line AB
    length = np.dot(diff,n)*n

    #Get the distance from P to the projected line on AB
    # To understand this we can imagine these as vector points
    # where the projected line + (diff - length) would give P
    D = np.linalg.norm(diff - length)
    
    #get point C, this is just to get the interpolation point that's actually 
    # on the line.
    C = A - length #negative because A length is a vector from C -> A

    #get the non-zero indices so that when dividing we don't get nans
    # non_zero_CA should = non_zero_BA, might be worth adding a check 
    # for that in future
    non_zero_CA = np.where(C-A != 0)

    #get f of minimum D
    f = np.mean(np.abs((C-A)[non_zero_CA]/(B-A)[non_zero_CA])) #should be the same for all though, this is not like...totally correct
                                        # but should be correct enough for this
    return(D,f)

def vectorize_dtypes() -> dict[str, np.array]:
    """Returns the vector space of damage types
    
    Returns
    -------
    dict
        keys: Name of the Damage type
        values: np.array of the damage type as its aspect vector
    """
    path = os.path.join(resources.files(aspects), 'dtype_aspects.json')
    with open(path, 'r', encoding='utf-8') as f:
        aspects_definition = json.load(f)
    return {k:attribute_to_coords(v) for k, v in aspects_definition.items()}

def check_native_types(natives: dict[str, np.ndarray], point: np.ndarray) -> bool:
    """Checks that our interpolated type isn't an already existing damage type
    
    Parameters
    ----------
    natives: dict[str, np.ndarray]
        dictionary of the native damage types
    point: np.ndarray
        the point to compare against
    
    Returns
    -------
    bool
        Indicates that the point was a native damage type
    """
    for k, v in natives.items():
        if l1_distance(v, point) < 1e-6:
            print(f'This is the same as DMG type {k}')
            return True
    return False

def convert_array(vec: np.ndarray) -> list[str]:
    """Converts from the numerical representation of the aspects
    back into the human readable strings"""
    types = []
    for i,entry in enumerate(list(vec)):
        if entry == 0:
            continue
        while entry < 0:
            types.append(NEGATIVES[i])
            entry += 1
        while entry > 0:
            types.append(POSITIVES[i])
            entry -= 1
    return types

if __name__ == "__main__":
    dtype_vectors = vectorize_dtypes()
    found_points = {}
    for a, b in itertools.combinations(dtype_vectors, 2):
        viable_points = simple_search_interpolation(dtype_vectors[a],
                                                    dtype_vectors[b])
        if len(viable_points) > 0:
            found_points[(a, b)] = viable_points

    for (a, b), viable_points in found_points.items():
        print('-'*20)
        print(f'Intermediate Damage Type of {a}-{b}')
        for pp in viable_points:
            if not check_native_types(dtype_vectors, pp['point']):
                print(f"interpolated coord: {pp['point']} \t @ f= {pp['interp_frac']:.2f}")
                print(f"interpolated aspects:{convert_array(pp['point'])}")
    # test_json = read_json(r"aspects\dtype_aspects.json")
    # print(test_json)
    # dtype1 = attribute_to_coords(test_json["Cold"])
    # dtype2 = attribute_to_coords(test_json["Necrotic"])
    # print("Cold: ",dtype1)
    # print("Necrotic: ",dtype2)
    # passed_points,err,F = test_interpolation(dtype1,dtype2)
    # print("---------------")
    # for i,pp in enumerate(passed_points):
        # D,f = get_nearest_f(dtype1,dtype2,pp)
        # print(f"interpolated coord: {pp} \t @ f= {f:.2f}\t ΔE= {D:.4f}")
    