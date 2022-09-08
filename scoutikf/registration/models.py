from re import M
from unicodedata import name
from django.db import models
from .storage import OverwriteStorage
from PIL import Image

from django.core.validators import FileExtensionValidator
# Create your models here.


class MasterCategory(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    en = models.CharField(max_length=100, null=True)
    include = models.BooleanField(null=True, default=False, db_index=True)

    def __repr__(self) -> str:
        return str(self.en)

    def __str__(self) -> str:
        return str(self.en)
    class Meta:
        verbose_name=("Master Category")
        verbose_name_plural=("Master Categories")

class MasterRoles(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    en = models.CharField(max_length=100, null=True)
    include = models.BooleanField(null=True, default=False, db_index=True)

    def __repr__(self) -> str:
        return str(self.en)

    def __str__(self) -> str:
        return str(self.en)
    class Meta:
        verbose_name=("Master Role")
        verbose_name_plural=("Master Roles")


class MasterSeason(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    en = models.CharField(max_length=100, null=True)
    year = models.IntegerField(null=True)
    include = models.BooleanField(null=True, default=False, db_index=True)

    def __repr__(self) -> str:
        return str(self.en)

    def __str__(self) -> str:
        return str(self.en)


class MasterState(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True,)
    name = models.CharField(max_length=200, null=True, db_index=True)
    country_id = models.CharField(max_length=300, null=True)
    include = models.BooleanField(null=True, default=False, db_index=True)

    def __repr__(self) -> str:
        return str(self.name)

    def __str__(self) -> str:
        return str(self.name)


class MasterCity(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    city = models.CharField(max_length=200, null=True, db_index=True)
    # state_id=models.IntegerField(null=True)
    state = models.ForeignKey(
        MasterState, null=True, verbose_name="State ID", on_delete=models.SET_NULL, db_index=True)
    include = models.BooleanField(null=True, default=False, db_index=True)

    def __repr__(self) -> str:
        return str(self.city)

    def __str__(self) -> str:
        return str(self.city)
    class Meta:
        verbose_name=("Master City")
        verbose_name_plural=("Master Cities")


class MasterPosition(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True,)
    position = models.CharField(max_length=200, null=True, db_index=True)
    label = models.CharField(max_length=200, null=True, db_index=True)
    type = models.CharField(max_length=200, null=True, db_index=True)

    def __repr__(self) -> str:
        return str(self.label)

    def __str__(self) -> str:
        return str(self.label)

class MasterDateLimit(models.Model):
    id = models.CharField(max_length=150, primary_key=True, db_index=True)

    lowerlimit = models.DateField(db_index=True)
    upperlimit = models.DateField(db_index=True)
    season = models.ForeignKey(
        MasterSeason, null=True, verbose_name="master_season_id_limit", db_index=True, on_delete=models.SET_NULL)


    def __repr__(self) -> str:
        return str(self.id)

    def __str__(self) -> str:
        return str(self.id)
class MasterGroup(models.Model):
    id = models.CharField(max_length=150, primary_key=True, db_index=True)
    group = models.CharField(max_length=300, null=True, db_index=True)
    year = models.CharField(max_length=300, null=True, db_index=True)
    start = models.DateField(db_index=True)
    end = models.DateField(db_index=True)
    include = models.BooleanField(null=True, default=True, db_index=True)
    orderid = models.IntegerField(null=True)
    gender = models.CharField(max_length=100, default="Female", db_index=True)

    def __repr__(self) -> str:
        return str(self.id)

    def __str__(self) -> str:
        return str(self.id)


class MasterGroupCity(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    cityid = models.ForeignKey(
        MasterCity, null=True, verbose_name="master_city_id", db_index=True, on_delete=models.SET_NULL)
    groupid = models.ForeignKey(
        MasterGroup, null=True, verbose_name="master group id", db_index=True, on_delete=models.SET_NULL)

    include = models.BooleanField(null=True, default=True, db_index=True)

    def __repr__(self) -> str:
        return str(self.id)

    def __str__(self) -> str:
        return str(self.id)
    class Meta:
        verbose_name=("Master Group City")
        verbose_name_plural=("Master Group Cities")


class MasterLabels(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    keydata = models.CharField(max_length=200, null=True, db_index=True)
    en = models.TextField(null=True, blank=True,)
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
        verbose_name=("Master Label")
        verbose_name_plural=("Master Labels")


class MasterDocument(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    keydata = models.CharField(max_length=200, null=True, db_index=True)
    en = models.CharField(max_length=300,blank=True, null=True)
    hi = models.CharField(max_length=300,blank=True, null=True)
    mr = models.CharField(max_length=300,blank=True, null=True)
    asm = models.CharField(max_length=300,blank=True, null=True)
    ben = models.CharField(max_length=300,blank=True, null=True)
    odia = models.CharField(max_length=300,blank=True, null=True)
    bodo = models.CharField(max_length=300,blank=True, null=True)
    include = models.BooleanField(null=True,blank=True, default=True, db_index=True)

    def __repr__(self) -> str:
        return str(self.en)

    def __str__(self) -> str:
        return str(self.en)


class MasterColumn(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    columnid = models.CharField(max_length=300,blank=True, null=True, db_index=True)
    label_key = models.CharField(max_length=300,blank=True, null=True)
    includep1 = models.BooleanField(null=True,blank=True, default=True, db_index=True)
    includep2 = models.BooleanField(null=True,blank=True, default=True, db_index=True)
    type = models.CharField(max_length=300,blank=True, null=True)
    orderid = models.IntegerField(null=True,blank=True,)


# class Coach(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     userid = models.CharField(max_length=300)
#     password = models.CharField(max_length=300)
#     first_name = models.CharField(max_length=300, null=True)
#     last_name = models.CharField(max_length=300, null=True)
#     mobile = models.CharField(max_length=10, unique=True, default="")
#     email = models.EmailField(null=True)
#     academy = models.CharField(max_length=300, null=True)

class ScoutCourse(models.Model):
    id = models.CharField(max_length=100, primary_key=True,db_index=True)
    course=models.TextField(null=True, blank=True,)
    amount = models.CharField(max_length=100,null=True,blank=True)
    extra=models.CharField(max_length=100,null=True, blank=True,)
class ScoutDiscountType(models.Model):
    id = models.CharField(max_length=100, primary_key=True,db_index=True)
    type=models.CharField(max_length=100,null=True, blank=True,)
    length=models.CharField(max_length=100,null=True, blank=True,)
    extra=models.CharField(max_length=100,null=True, blank=True,)

class ScoutCourseDiscount(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    course=models.ForeignKey(ScoutCourse,null=True, verbose_name="ScoutCourses", db_index=True, on_delete=models.SET_NULL)
    type = models.ForeignKey(
    ScoutDiscountType, null=True, verbose_name="ScoutDiscountTypes", db_index=True, on_delete=models.SET_NULL)
    discount=models.CharField(max_length=100,null=True, blank=True,)
      
class Scout(models.Model):
    id = models.BigAutoField(primary_key=True)
    
    associated_years = models.CharField(max_length=100,blank=True,)
    associated_as = models.CharField(max_length=200,blank=True,)

    referral = models.CharField(max_length=100,blank=True,)
    discount = models.CharField(max_length=100,blank=True,)
    course = models.ForeignKey( 
        ScoutCourse, null=True, verbose_name="Course", db_index=True, on_delete=models.SET_NULL)



#   tournament city
    city = models.ForeignKey( 
        MasterCity, null=True, verbose_name="master city", db_index=True, on_delete=models.SET_NULL)
    state = models.ForeignKey(
        MasterState, null=True, verbose_name="master state", related_name='state2', db_index=True, on_delete=models.SET_NULL)

#   profile
    gender = models.CharField(max_length=200, null=True, db_index=True)
    first_name = models.CharField(max_length=300, null=True)
    last_name = models.CharField(max_length=300, null=True)




#   Contact Information
    mobile = models.CharField(max_length=10, null=True, default="")

    email = models.EmailField(null=True,blank=True,)
    ipv4 = models.GenericIPAddressField(max_length=100,blank=True, null=True)
    ipv6 = models.GenericIPAddressField(max_length=100,blank=True, null=True)
    ikfuniqueid = models.CharField(max_length=200, null=True, db_index=True)
    playeruploadid=models.CharField(max_length=250, null=True, db_index=True)



    dob = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    status = models.CharField(max_length=10, null=True,blank=True, db_index=True)

    season = models.ForeignKey(
        MasterSeason, null=True, verbose_name="master_season_id", db_index=True, on_delete=models.SET_NULL)


    order_id = models.CharField(max_length=300,blank=True, null=True)

    status = models.CharField(max_length=10, null=True,blank=True, db_index=True)
    razorpay_order_id = models.CharField(max_length=300,blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=300,blank=True, null=True)
    razorpay_signature = models.CharField(max_length=400,blank=True, null=True)
    error_code = models.CharField(max_length=300,blank=True, null=True)
    error_description = models.CharField(max_length=400,blank=True, null=True)
    error_source = models.CharField(max_length=300,blank=True, null=True)
    error_reason = models.CharField(max_length=300,blank=True, null=True)
    error_meta_order_id = models.CharField(max_length=300,blank=True, null=True)
    error_meta_payment_id = models.CharField(max_length=300,blank=True, null=True)
    amount = models.CharField(max_length=100,blank=True, null=True)
    # name=first_name+last_name

    def __repr__(self) -> str:
        return str(self.first_name)

    def __str__(self) -> str:
        return str(self.first_name)




class Upload(models.Model):
    unique = models.CharField(max_length=400, null=True, db_index=True)
    image = models.ImageField(storage=OverwriteStorage(), upload_to='images')
    fname = models.CharField(max_length=300, null=True,default="")
    lname = models.CharField(max_length=300, null=True,default="")
    mobilenumberupload = models.CharField(max_length=10, null=True, default="")
    

    def __str__(self):
        return str(self.pk)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)


class Uploadfile(models.Model):
    unique = models.CharField(max_length=400, null=True, db_index=True)
    fname = models.CharField(max_length=300, null=True)
    lname = models.CharField(max_length=300, null=True)
    mobilenumberupload = models.CharField(max_length=10, null=True)
    file = models.ImageField(
        storage=OverwriteStorage(), upload_to='documents',)

    def __str__(self):
        return str(self.pk)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.file.path)
        if img.height > 440 or img.width > 440:
            output_size = (440, 440)
            img.thumbnail(output_size)
            img.save(self.file.path)


class MasterAmount(models.Model):
    id = models.BigAutoField(primary_key=True, db_index=True)
    city = models.ForeignKey(
        MasterCity, null=True, verbose_name="master_city_id", db_index=True, on_delete=models.SET_NULL)
    season = models.ForeignKey(
        MasterSeason, null=True, verbose_name="master_season_id", db_index=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(
        MasterCategory, null=True, verbose_name="master_category_id", db_index=True, on_delete=models.SET_NULL)
    group = models.ForeignKey(
        MasterGroup, null=True, verbose_name="master_group_id", db_index=True, on_delete=models.SET_NULL)
    coach_or_player = models.ForeignKey(
        MasterRoles, null=True, verbose_name="master_roles_id", db_index=True, on_delete=models.SET_NULL)
    amount = models.CharField(max_length=100, null=True)
    discount = models.CharField(max_length=100, null=True)

    include = models.BooleanField(null=True, default=True, db_index=True)

class MasterPartner(models.Model):
    id = models.CharField(max_length=100, primary_key=True,db_index=True)
    partner_name = models.CharField(max_length=300, null=True)
    mobile = models.CharField(max_length=100, null=True)
    email=models.EmailField(max_length=300,null=True)
    address=models.CharField(max_length=300,null=True)
    city= models.ForeignKey(
        MasterCity, null=True, verbose_name="master_city_id", db_index=True, on_delete=models.SET_NULL)
    season = models.ForeignKey(
        MasterSeason, null=True, verbose_name="master_season_id", db_index=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(
        MasterCategory, null=True, verbose_name="master_category_id", db_index=True, on_delete=models.SET_NULL)
    dateofevent=models.DateField(null=True,db_index=True)

    
    include = models.BooleanField(null=True, default=True, db_index=True)
#user=models.ForeignKey(User,null=True,  verbose_name="files", on_delete=models.CASCADE)














