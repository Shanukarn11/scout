from re import M
from tabnanny import verbose
from unicodedata import name
from django.db import models

from registration.models import MasterCity, MasterState
from .storage import OverwriteStorage
from PIL import Image

from django.core.validators import FileExtensionValidator
# Create your models here.

class MasterCoachLabels(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    keydata = models.CharField(max_length=200,blank=True, null=True, db_index=True)
    en = models.TextField(blank=True,null=True)
    hi = models.TextField(blank=True,null=True)
    mr = models.TextField(blank=True,null=True)
    asm = models.TextField(blank=True,null=True)
    ben = models.TextField(blank=True,null=True)
    odia = models.TextField(blank=True,null=True)
    bodo = models.TextField(blank=True,null=True)

    extrainfo = models.CharField(max_length=200,blank=True, null=True)

    def __repr__(self) -> str:
        return str(self.en)

    def __str__(self) -> str:
        return str(self.en)
    class Meta:
        verbose_name=("Master Coach Label")
        verbose_name_plural=("Master Coach Labels")

class CoachModel(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    coach_name = models.CharField(max_length=200, null=False, db_index=False)
    coach_email = models.CharField(max_length=200, null=False, db_index=False)
    coach_mobile = models.CharField(max_length=10, null=False, db_index=True,unique=True)
    coach_id = models.CharField(max_length=200, null=True, db_index=True,unique=True)
    tournament_city = models.ForeignKey( 
        MasterCity, null=True, verbose_name="master city", db_index=True, on_delete=models.SET_NULL)
    tournament_state = models.ForeignKey(
        MasterState, null=True, verbose_name="master state", db_index=True, on_delete=models.SET_NULL)
    academy_name = models.CharField(max_length=200, null=True, db_index=False)
    academy_email = models.CharField(max_length=200, null=True, db_index=False)
    academy_mobile = models.CharField(max_length=200, null=True, db_index=False)
    barcode_url=models.CharField(max_length=200, null=True, db_index=False)

    class Meta:
        verbose_name=("CoachModel")
        verbose_name_plural=("CoachModels")