#!/usr/bin/env python
"""
Script for manual enroll students in edx-adapt application.

Student's anonymous ids are downloaded from Edx lms Course/Instructor/Data Download/ page as csv file.
Sample of such file is located in edx-adapt/data dir.

Default values for optional parameters --host, --port, --course are taken from config.py file. If script is used
locally without config.py file nearby, optional parameters: --host, --port, --course become mandatory.
Additionally could be set optional parameters --prob and --skills if default values are not appropriate.
"""
import argparse
import csv
import json
import os
import sys

import requests

try:
    from config import EDXADAPT
    REQUIRED_PARAMS = False
except ImportError:
    REQUIRED_PARAMS = True

DEFAULT_PROBABILITIES = {'pg': 0.25, 'ps': 0.25, 'pi': 0.1, 'pt': 0.5, 'threshold': 0.99}

DEFAULT_SKILLS = ['center', 'shape', 'spread', 'x axis', 'y axis', 'h to d', 'd to h', 'histogram', 'None']


def get_parameters(required=REQUIRED_PARAMS):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter, description='Enroll students from csv file.'
    )

    parser.add_argument('csvfile', metavar='file.csv', type=str, help='path/to/csv/file with anonymous student ids.')

    parser.add_argument(
        '--host',
        dest='host',
        type=str,
        default=EDXADAPT['HOST'] if not required else None,
        required=required,
        help='host of the edx-adapt server.'
    )
    parser.add_argument(
        '--port',
        dest='port',
        type=int,
        default=EDXADAPT['PORT'] if not required else None,
        required=required,
        help='port of the edx-adapt server.'
    )
    parser.add_argument(
        '--course',
        dest='course_id',
        type=str,
        default=EDXADAPT['COURSE_ID'] if not required else None,
        required=required,
        help='course student is enrolled in.'
    )
    parser.add_argument(
        '--prob',
        dest='probabilities',
        type=json.loads,
        default=DEFAULT_PROBABILITIES,
        help=(
            'dict with BKT model probabilities student will be enrolled with, default is '
            '\'{"pg": 0.25, "ps": 0.25, "pi": 0.1, "pt": 0.5, "threshold": 0.99}\''
        )
    )
    parser.add_argument(
        '--skills',
        dest='skills',
        type=str,
        nargs='+',
        default=DEFAULT_SKILLS,
        help=(
            'sequence with skills student will be enrolled with, default are: '
            '"center" "shape" "spread" "x axis" "y axis" "h to d" "d to h" "histogram" "None"'
        )
    )
    params = parser.parse_args()
    return vars(params)


def get_students_for_enrollment(path_to_file):
    """
    Parse csv file with student anonymous data and prepare a list of students for enrollment in edx-adapt.
    """
    if not os.path.exists(path_to_file):
        print("File with path: {} does not exist, please try again".format(path_to_file))
        sys.exit()
    with open(path_to_file) as csvfile:
        raw_students_ids = csv.DictReader(csvfile)
        for line in raw_students_ids:
            yield line['Anonymized User ID']


def get_enrolled_students(headers, **kwargs):
    """
    Get student already enrolled in edx-adapt.
    """
    users = requests.get('http://{host}:{port}/api/v1/course/{course_id}/user'.format(**kwargs), headers=headers)
    if users:
        users = users.json()
        return set(users['users']['finished']) | set(users['users']['in_progress'])
    else:
        print("Course or edx-adapt server is not found")
        sys.exit()


def main():
    parameters = get_parameters()
    student_id_list = get_students_for_enrollment(parameters['csvfile'])
    headers = {'Content-type': 'application/json'}
    enrolled_students = get_enrolled_students(headers, **parameters)

    for student_id in student_id_list:
        if student_id not in enrolled_students:
            payload = {'user_id': student_id}
            requests.post(
                'http://{host}:{port}/api/v1/course/{course_id}/user'.format(**parameters),
                json=payload,
                headers=headers
            )
            print("student {} is enrolled in course {}".format(student_id, parameters['course_id']))
            payload = {
                'course_id': parameters['course_id'],
                'params': parameters['probabilities'],
                'user_id': student_id,
                'skills_list': parameters['skills']
            }
            requests.post(
                'http://{host}:{port}/api/v1/parameters/bulk'.format(**parameters), json=payload, headers=headers
            )
            print("student's skill are added")


if __name__ == '__main__':
    main()
