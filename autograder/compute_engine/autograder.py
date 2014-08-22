#!/usr/bin/env python3

import tempfile
import os
import shutil

from apiclient.discovery import build

PROJECT_NAME = 'ok-server'
TASK_QUEUE = 'autograder-queue'
LEASE_SECS = 60*10 # 10 minutes

def lease_task_from_queue(task_api):
  """Gets the available tasks from the taskqueue.

  Returns:
    Lease response object.
  """
  try:
    tasks_to_fetch = 1
    lease_req = self.task_api.tasks().lease(project=PROJECT_NAME,
                                            taskqueue=TASK_QUEUE,
                                            leaseSecs=LEASE_SECS,
                                            numTasks=tasks_to_fetch,
                                            body={})
    result = lease_req.execute()
    return result
  except HttpError, http_error:
    logger.error('Error during lease request: %s' % str(http_error))
    return None

class Task(object):
    def __init__(self, files):
        self._files = files
        self.directory = None
        self.assignment = 'hw1'

    def setup_files(self):
        self.directory = tempfile.mkdtemp()
        autograder_root = os.getcwd()
        os.chdir(self.directory)
        os.mkdir(self.assignment)
        os.chdir(self.assignment)
        self.dump_files()
        shutil.copy(os.path.join(autograder_root,'..', 'ok.py'),
                    self.directory)

    def dump_files(self):
        for fle, contents in self.files.iteritems():
            with open(fle, 'w') as f:
                f.write(contents)

    def run_tests(self):
        os.chdir(self.directory)
        import ok
        ok.main()

    def upload_results(self):
        pass

def get_tasks(task_api):
    leased_tasks = lease_task_from_queue(task_api)
    if not leased_tasks:
        return leased_tasks

    return [Task(leased_task) for leased_task in leased_tasks]

def main():
    task_api = build('taskqueue', 'v1beta2')
    while True:
        tasks = get_task(task_api)
        if tasks:
            for task in tasks:
                task.setup_files()
                task.run_tests()
                task.upload_results()
        else:
            print('error or no tasks', tasks)

if __nome__ == "__main__":
    main()
