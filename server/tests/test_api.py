#!/usr/bin/env python
# encoding: utf-8
#pylint: disable=no-member, no-init
"""
tests.py

"""
import unittest

from basetest import BaseTestCase #pylint: disable=relative-import

from app.api import API_PREFIX
from app import models, constants

import io

def _dict_unicode(obj):
    if isinstance(obj, dict):
        return {unicode(key): value for
                key, value in obj.iteritems()}
    else:
        return sorted([_dict_unicode(item) for item in obj])

class APITest(object): #pylint: disable=no-init
    """
    Simple test case for the API
    """
    model = None
    name = ""
    num = 1

    @classmethod
    def get_basic_instance(cls):
        """
        Gets a basic instance of the model class
        """
        raise NotImplementedError()

    def setUp(self): #pylint: disable=super-on-old-class, invalid-name
        """Set up"""
        super(APITest, self).setUp()
        self.inst = self.get_basic_instance()

    def get(self, url, *args, **kwds):
        """
        Utility method to do a get request
        """
        self.response = self.client.get(API_PREFIX + url, *args, **kwds)
        try:
            self.response_json = models.json.loads(self.response.data)
        except Exception:
            self.response_json = None

    def get_index(self, *args, **kwds):
        """
        Utility method to do a get on the index
        """
        self.get('/{}'.format(self.name), *args, **kwds)

    def get_entity(self, inst, *args, **kwds):
        """
        Utility method to do a get on a particular instance
        """
        self.get('/{}/{}'.format(self.name, inst.key.id()), *args, **kwds)

    def post(self, url, **kwds):
        """
        Utility method to do a post request, with json
        """
        kwds.setdefault('content_type', 'application/json')
        print kwds
        self.response = self.client.post(API_PREFIX + url, **kwds)
        try:
            self.response_json = models.json.loads(self.response.data)
        except Exception as e:
            self.response_json = None

    def post_json(self, url, **kwds):
        """
        Utility method for posting JSON
        """
        data = kwds.pop('model', {})
        if isinstance(data, models.Base):
            data = data.to_dict()

        if 'file' in kwds:
            data['file'] = kwds.pop('file')
        else:
            data = models.json.dumps(data)
        kwds['data'] = data
        kwds.setdefault('content_type', 'application/json')
        self.post(url, **kwds)

    def post_entity(self, inst, *args, **kwds):
        """
        Posts an entity to the server
        """
        self.post_json('/{}/new'.format(self.name), model=inst, **kwds)
        if inst.key:
            if self.response_json.get('key'):
                self.assertEqual(inst.key.id(), self.response_json['key'])
        else:
            inst.key = models.ndb.Key(self.model, self.response_json.get('key'))
        self.assertStatusCode(200)

    ## ASSERTS ##

    def assertStatusCode(self, code): #pylint: disable=invalid-name
        """ Asserts that the status code was `code`"""
        self.assertEqual(self.response.status_code, code)

    def assertJson(self, correct_json): #pylint: disable=invalid-name
        """Asserts that the response was |correct_json|"""
        self.assertStatusCode(200)
        self.assertEqual(_dict_unicode(self.response_json), _dict_unicode(correct_json))

    ## INDEX ##
    def test_index_empty(self):
        """ Tests there are no entities when the db is created """
        self.get('/{}'.format(self.name))
        self.assertJson([])

    def test_index_one_added(self):
        """ Tests that the index method gives me an entity I add """
        self.inst.put()
        self.get_index()
        self.assertJson([self.inst.to_dict()])

    def test_index_one_removed(self):
        """Tests that removing an entity makes it disappear from the index """
        self.inst.put()
        self.get_index()
        self.assertJson([self.inst.to_dict()])

        self.inst.key.delete()
        self.get_index()
        self.assertJson([])

    def test_index_one_removed_from_two(self):
        """
        Test that removing one item out of two in the DB makes sure
        the other item is still found"""
        self.inst.put()
        inst2 = self.get_basic_instance()
        inst2.put()
        self.get_index()
        self.assertJson(sorted([self.inst.to_dict(), inst2.to_dict()]))

        inst2.key.delete()
        self.get_index()
        self.assertJson([self.inst.to_dict()])

    ## ENTITY GET ##
    def test_get_basic(self):
        """ Tests that a basic get works """
        self.inst.put()
        self.get_entity(self.inst)
        self.assertJson(self.inst.to_dict())

    def test_get_with_two_entities(self):
        """
        Testing that getting one entity with two in the DB gives the
        right one """
        self.inst.put()
        inst2 = self.get_basic_instance()
        inst2.put()

        self.get_entity(inst2)
        self.assertJson(inst2.to_dict())

    def test_get_invalid_id_errors(self):
        """ Tests that a get on an invalid ID errors """
        self.get('/{}/1'.format(self.name))
        self.assertStatusCode(404)

    ## ENTITY POST ##
    def test_entity_create_basic(self):
        """Basic test to see if you can create an empty entity"""
        self.post_entity(self.inst)
        self.assertStatusCode(200)

        gotten = self.model.get_by_id(self.response_json['key'])
        self.assertEqual(gotten, self.inst)

    ## ENTITY PUT ##

    ## ENTITY DELETE ##

class UserAPITest(APITest, BaseTestCase):
    """User API test"""
    model = models.User
    name = 'users'

    num = 1
    @classmethod
    def get_basic_instance(cls):
        rval = models.User(email=str(cls.num) + u'test@example.com',
                           login=u'cs61a-ab', role=constants.STUDENT_ROLE,
                           first_name=u"Joe", last_name=u"Schmoe")
        cls.num += 1
        return rval

class AssignmentAPITest(APITest, BaseTestCase):
    """ Assignment API test"""
    model = models.Assignment
    name = 'assignments'

    num = 1
    @classmethod
    def get_basic_instance(cls):
        rval = models.Assignment(name=u'proj' + str(cls.num), points=3)
        cls.num += 1
        return rval

class SubmissionAPITest(APITest, BaseTestCase):
    """ Assignment API test"""
    model = models.Submission
    name = 'submissions'

    def setUp(self):
        super(SubmissionAPITest, self).setUp()
        self.project_name = u'test Project'
        self.project = models.Assignment(name=self.project_name, points=3,
                submissions=[self.inst])
        self.project.put()

    def get_basic_instance(self):
        rval = models.Submission(location='whatisthis' + str(self.num))
        self.num += 1
        return rval

    def post_entity(self, inst, *args, **kwds):
        """
        Posts an entity to the server
        """
        data = inst.to_dict()
        data['project_name'] = kwds.pop('project_name', self.project_name)
        self.post_json('/{}/new'.format(self.name), model=data, *args, **kwds)
        if inst.key:
            if self.response_json.get('key'):
                self.assertEqual(inst.key.id(), self.response_json['key'])
        else:
            inst.key = models.ndb.Key(self.model, self.response_json.get('key'))

    def test_invalid_student_submission(self):
        self.project_name = 'blahblah'
        self.post_entity(self.inst)

        self.assertStatusCode(422)

    def test_file_upload(self):
        self.client.open(method='POST', data={'foo': 'this is some text',
           'file': (io.BytesIO(b'my file contents'), 'test.txt')})
        # self.post_json('/{}/new'.format(self.name),
         #       file=(io.BytesIO(b'test file'), 'file.txt'))
        # print self.response
        data = self.inst.to_dict()
        data['upload_var'] = (io.BytesIO(b'my file contents'), 'test.txt')
        print data
        self.client.post('/api/v1/submissions/new', data=data)
        print self.response.data

if __name__ == '__main__':
    unittest.main()
