import random
import pandas as pd
import json


def add_person_to_course(course_dict, course_name, person_name):
    if course_name not in course_dict.keys():
        course_dict[course_name] = [person_name]
    else:
        course_dict[course_name].append(person_name)


def load_config(path):
    with open(path, 'r') as f:
        conf = json.load(f)
    return conf


def load_data(path):
    dats = pd.read_csv(path)
    return dats


def sanity_check(dats):
    if not len(dats.Név.unique()) == len(dats.Név):
        exit(1)
    # TODO:
    #   add sanity check for duplicate entries in a row


def reformat_data(dats):
    dats.rename(columns={'Beszámoló nélkül?': 'Beszámoló nélkül?.0',
                         'Hány kurzust szeretnél felvenni az őszi félévben? (a kötelező sávoson kívül)': 'Hány '
                                                                                                         'beszámoló '
                                                                                                         'ősszel',
                         'Hány kurzust szeretnél felvenni a tavaszi félévben? (a kötelező sávoson kívül)': 'Hány '
                                                                                                           'beszámoló '
                                                                                                           'tavasszal'},
                inplace=True)

    dats['Aktív kurzusok ősszel'] = 0
    dats['Aktív kurzusok tavasszal'] = 0
    

def ranking(dats, seed):
    num_of_people = dats.shape[0]

    random.seed(seed)
    lucks = []
    for index in range(num_of_people):
        lucks += [(index, random.random())]

    lucks.sort(key=lambda x: x[1], reverse=True)
    ordered_lucks = []
    for rank, luck in enumerate(lucks):
        ordered_lucks += [(luck[0], luck[1], rank)]

    ordered_lucks.sort(key=lambda x: x[0])
    _, _, rank = zip(*ordered_lucks)

    dats['rank'] = pd.Series(rank).values

    dats.set_index('rank', inplace=True)
    

def assignment(cfg, dats):
    num_of_people = dats.shape[0]

    courses = {}
    courses2 = {}

    datsdict = dats.to_dict()

    for preference_num in map(lambda x: str(x), range(1, 11)):
        # determine the order in which we iterate through people
        if int(preference_num) % 2:
            order = range(num_of_people)
        else:
            order = reversed(range(num_of_people))

        # for each person in the order of ranks
        for rank in order:
            course = datsdict[preference_num + '. kurzus'][rank]
            if pd.isnull(course):
                continue
            person = datsdict['Név'][rank]
            if pd.isnull(datsdict['Beszámoló nélkül?.' + str(int(preference_num) - 1)][rank]):
                # if the person is already on the number of courses he/she wants to be on, ignore this step
                if (course in cfg['courses']['fall']
                    and datsdict['Aktív kurzusok ősszel'][rank] == datsdict['Hány beszámoló ősszel'][rank]) \
                        or (course in cfg['courses']['spring']
                            and datsdict['Aktív kurzusok tavasszal'][rank] == datsdict['Hány beszámoló tavasszal'][
                                rank]):
                    continue

                # add person to given course
                add_person_to_course(courses, course, person)
                # if the given course was not full before, increment the active courses for the person
                if len(courses[course]) <= cfg['limits'][course]:
                    if course in cfg['courses']['fall']:
                        datsdict['Aktív kurzusok ősszel'][rank] += 1
                    if course in cfg['courses']['spring']:
                        datsdict['Aktív kurzusok tavasszal'][rank] += 1
            else:
                add_person_to_course(courses2, course, person)

    for course in courses2.keys():
        courses2[course] = ['{0} (besz. nélk.)'.format(attendant) for attendant in courses2[course]]

    return courses, courses2


def merging(courses1, courses2):
    for course in set.intersection(set(courses1.keys()), set(courses2.keys())):
        courses1[course] += courses2[course]
    for course in list(set(courses2.keys()) - set(courses1.keys())):
        courses1[course] = courses2[course]

    return courses1


def formatting(cfg, courses):
    all_courses = (cfg['courses']['fall'] + cfg['courses']['spring'])
    maxval = max(map(lambda x: len(x), courses.values()))
    for course in [c for c in all_courses if c not in courses.keys()]:
        courses[course] = []
    for attendant_list in courses.values():
        attendant_list.extend(['']*(maxval-len(attendant_list)))
    df = pd.DataFrame.from_dict(courses)
    # for course in all_courses:
    #     if course not in df.columns:
    #         all_courses.remove(course)
    df = df[all_courses]
    return df


if __name__ == '__main__':
    config = load_config('config.json')
    data = load_data('C:\\Users\Levente Dologh\workspace\szisz\pre-app.csv')
    sanity_check(data)
    reformat_data(data)
    ranking(data, 12345678)
    merged = merging(*assignment(config, data))
    output = formatting(config, merged)
    print(output)