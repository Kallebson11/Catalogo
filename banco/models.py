from django.db import models

class Despesas (models.Model):
    id_deputado			=models.IntegerField() 
    ano				    =models.IntegerField()
    mes				    =models.IntegerField()
    tipo_despesa		=models.CharField(max_length = 200)
    id_documento		=models.IntegerField(primary_key=True)
    nome_fornecedor	    =models.CharField(max_length = 300)
    cnpj_cpf_fornecedor =models.CharField(max_length = 20)
    valor_documento	    =models.DecimalField(max_digits=15, decimal_places=2)
    valor_glosa		    =models.DecimalField(max_digits=15, decimal_places=2)
    valor_liquido		=models.DecimalField(max_digits=15, decimal_places=2)
    data_carga			=models.DateTimeField()


    class Meta:
        verbose_name = "Despesas"
        verbose_name_plural = "Despesas"
        db_table = "[stage].[despesas]"


class Deputados (models.Model):
    id				= models.IntegerField(primary_key=True)
    nome			= models.TextField(max_length=200)
    sigla_partido	= models.TextField(max_length=20)
    sigla_uf		= models.CharField(max_length=2)
    id_legislatura	= models.IntegerField()
    data_carga		= models.DateTimeField()

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Deputados"
        verbose_name_plural = "Deputados"
        db_table = "[stage].[deputados]"


class Partidos (models.Model):
    id			= models.IntegerField(primary_key=True)
    sigla		= models.CharField(max_length=20, default='')
    nome		= models.TextField(max_length=200)
    data_carga	= models.DateTimeField()

    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Partidos"
        verbose_name_plural = "Partidos"
        db_table = "[stage].[partidos]"


class LogCarga(models.Model):

    STATUS_CHOICES = [
        ("S", "Sem erro"),
        ("E", "Erro"),
    ]

    id              = models.AutoField(primary_key=True)
    inicio          = models.DateTimeField()
    fim             = models.DateTimeField(null=True, blank=True)
    endpoint        = models.CharField(max_length=255)
    ano             = models.IntegerField()
    lidos           = models.IntegerField(default=0)
    inseridos       = models.IntegerField(default=0)
    atualizados     = models.IntegerField(default=0)
    status          = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default="S",
    )
    erro            = models.TextField(null=True, blank=True)

        
    class Meta:
        verbose_name = "LogCarga"
        verbose_name_plural = "LogCargas"
        db_table = "[stage].[log_carga]"