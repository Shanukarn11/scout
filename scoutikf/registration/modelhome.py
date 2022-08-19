from django.db import models


class SocialMediaLink(models.Model):
    id = models.BigAutoField(primary_key=True,db_index=True)
    name=models.CharField(max_length=200,null=True,db_index=True)
    icon=models.CharField(max_length=200,null=True)
    url=models.CharField(max_length=300,null=True)
    type_of_link=models.CharField(max_length=100,null=True,db_index=True)
    include=models.BooleanField(null=True,default=True,db_index=True)

# class NoticeBoard(models.Model):
#     id = models.BigAutoField(primary_key=True,db_index=True)
#     title=models.CharField(max_length=200,null=True,db_index=True)
#     description=models.JSONField(null=True)
#     include=models.BooleanField(null=True,default=True,db_index=True)
#     isHeading=models.BooleanField(null=True,default=False,db_index=True)