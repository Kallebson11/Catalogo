USE [CATALOGO]
GO

/****** Object:  Table [stage].[deputados]    Script Date: 16/11/2026 22:07:48 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [stage].[deputados](
	[id] [int] NOT NULL,
	[nome] [nvarchar](max) NOT NULL,
	[sigla_uf] [nvarchar](2) NOT NULL,
	[id_legislatura] [int] NOT NULL,
	[data_carga] [datetime2](7) NULL,
	[sigla_partido] [nvarchar](max) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

USE [CATALOGO]
GO

/****** Object:  Table [stage].[despesas]    Script Date: 16/11/2026 22:08:04 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [stage].[despesas](
	[id_deputado] [int] NULL,
	[ano] [int] NOT NULL,
	[mes] [int] NOT NULL,
	[id_documento] [int] NOT NULL,
	[nome_fornecedor] [nvarchar](300) NOT NULL,
	[cnpj_cpf_fornecedor] [nvarchar](20) NOT NULL,
	[valor_documento] [numeric](15, 2) NOT NULL,
	[valor_glosa] [numeric](15, 2) NOT NULL,
	[valor_liquido] [numeric](15, 2) NOT NULL,
	[data_carga] [datetimeoffset](7) NOT NULL,
	[tipo_despesa] [nvarchar](200) NOT NULL,
 CONSTRAINT [PK__stage.de__B9E37C188D577FA3] PRIMARY KEY CLUSTERED 
(
	[id_documento] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO

USE [CATALOGO]
GO

/****** Object:  Table [stage].[log_carga]    Script Date: 16/11/2026 22:08:20 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [stage].[log_carga](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[inicio] [datetimeoffset](7) NOT NULL,
	[fim] [datetimeoffset](7) NULL,
	[endpoint] [nvarchar](255) NOT NULL,
	[ano] [int] NOT NULL,
	[lidos] [int] NOT NULL,
	[inseridos] [int] NOT NULL,
	[atualizados] [int] NOT NULL,
	[status] [nvarchar](1) NOT NULL,
	[erro] [nvarchar](max) NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

USE [CATALOGO]
GO

/****** Object:  Table [stage].[partidos]    Script Date: 16/11/2026 22:08:29 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [stage].[partidos](
	[id] [int] NOT NULL,
	[nome] [nvarchar](max) NOT NULL,
	[data_carga] [datetimeoffset](7) NOT NULL,
	[sigla] [nvarchar](20) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO





