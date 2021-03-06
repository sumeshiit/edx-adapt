import flask
from flask import Flask
from flask.ext.cors import CORS
from flask_restful import Api
# import API resources
import edx_adapt.api.resources.course_resources as CR
import edx_adapt.api.resources.tutor_resources as TR
import edx_adapt.api.resources.data_serve_resources as DR
import edx_adapt.api.resources.model_resources as MR
# import data and model stuff
import edx_adapt.data.course_repository as repo
import edx_adapt.data.mongodb_storage as mongodbstore
from edx_adapt import logger
import edx_adapt.select.skill_separate_random_selector as select
import edx_adapt.model.bkt as bkt

app = Flask(__name__)
app.debug = False
CORS(app)
api = Api(app)

# TODO: load from settings
base = '/api/v1'

database = repo.CourseRepositoryMongo(mongodbstore.MongoDbStorage('mongodb://localhost:27017/'))
student_model = bkt.BKT()
selector = select.SkillSeparateRandomSelector(database, student_model, "user skill")

api.add_resource(CR.Courses, base + '/course',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(CR.Skills, base + '/course/<course_id>/skill',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(CR.Users, base + '/course/<course_id>/user',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(CR.Problems, base + '/course/<course_id>', base + '/course/<course_id>/skill/<skill_name>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(CR.Experiments, base + '/course/<course_id>/experiment',
                 resource_class_kwargs={'data': database, 'selector': selector})

api.add_resource(CR.Probabilities, base + '/course/<course_id>/probabilities',
                 resource_class_kwargs={'data': database, 'selector': selector})

api.add_resource(TR.UserInteraction, base + '/course/<course_id>/user/<user_id>/interaction',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(TR.UserProblems, base + '/course/<course_id>/user/<user_id>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(TR.UserPageLoad, base + '/course/<course_id>/user/<user_id>/pageload',
                 resource_class_kwargs={'data': database, 'selector': selector})

api.add_resource(DR.SingleProblemRequest, base + '/data/logs/course/<course_id>/user/<user_id>/problem/<problem_name>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(DR.UserLogRequest, base + '/data/logs/course/<course_id>/user/<user_id>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(DR.CourseLogRequest, base + '/data/logs/course/<course_id>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(DR.ExperimentLogRequest, base + '/data/logs/course/<course_id>/experiment/<experiment_name>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(DR.UserTrajectoryRequest, base + '/data/trajectory/course/<course_id>/user/<user_id>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(DR.CourseTrajectoryRequest, base + '/data/trajectory/course/<course_id>',
                 resource_class_kwargs={'data': database, 'selector': selector})
api.add_resource(
    DR.ExperimentTrajectoryRequest,
    base + '/data/trajectory/course/<course_id>/experiment/<experiment_name>',
    resource_class_kwargs={'data': database, 'selector': selector}
)

api.add_resource(MR.Parameters, base+'/parameters',
                 resource_class_kwargs={'data': database, 'selector': selector})

api.add_resource(MR.ParametersBulk, base+'/parameters/bulk',
                 resource_class_kwargs={'data': database, 'selector': selector})


@app.errorhandler(404)  # Return JSON with 404 instead of html
def page_not_found(e):
    return flask.jsonify(error=404, text=str(e)), 404


@app.before_request
def log_request_info():
    logger.debug('{request}\n{headers}{body}\n'.format(
        request=str(flask.request), headers=flask.request.headers, body=flask.request.get_data()
    ))


def run():
    app.run(host='0.0.0.0', port=8080, threaded=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
