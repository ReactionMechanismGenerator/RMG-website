from django.db import models


class RegressionTestJob(models.Model):

	developer = models.TextField(default='')

	pull_request = models.TextField(default='')

	rmgpy_branch = models.TextField(default='')

	rmgdb_branch = models.TextField(default='')

	job_status = models.TextField(default='')