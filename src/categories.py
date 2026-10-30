"""类目与州的中文映射（人工校对）。"""

# 商品类目：葡萄牙语 -> 中文
CATEGORY_ZH = {
    "beleza_saude": "美容健康",
    "informatica_acessorios": "电脑配件",
    "automotivo": "汽车用品",
    "cama_mesa_banho": "床品浴室",
    "moveis_decoracao": "家具装饰",
    "esporte_lazer": "运动休闲",
    "perfumaria": "香水香氛",
    "utilidades_domesticas": "家居日用",
    "telefonia": "手机通讯",
    "relogios_presentes": "手表礼品",
    "alimentos_bebidas": "食品饮料",
    "bebes": "母婴用品",
    "papelaria": "文具",
    "tablets_impressao_imagem": "平板打印影像",
    "brinquedos": "玩具",
    "telefonia_fixa": "固定电话",
    "ferramentas_jardim": "园艺工具",
    "fashion_bolsas_e_acessorios": "时尚箱包配饰",
    "eletroportateis": "小家电",
    "consoles_games": "游戏主机",
    "audio": "影音设备",
    "fashion_calcados": "时尚鞋履",
    "cool_stuff": "新奇小物",
    "malas_acessorios": "旅行箱包",
    "climatizacao": "空调暖通",
    "construcao_ferramentas_construcao": "建筑工具",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "厨卫餐厅花园家具",
    "construcao_ferramentas_jardim": "建筑园艺工具",
    "fashion_roupa_masculina": "男装",
    "pet_shop": "宠物用品",
    "moveis_escritorio": "办公家具",
    "market_place": "综合商城",
    "eletronicos": "电子产品",
    "eletrodomesticos": "家用电器",
    "artigos_de_festas": "派对用品",
    "casa_conforto": "家居舒适",
    "construcao_ferramentas_ferramentas": "建筑手动工具",
    "agro_industria_e_comercio": "农工商",
    "moveis_colchao_e_estofado": "床垫软包家具",
    "livros_tecnicos": "专业书籍",
    "casa_construcao": "家装建材",
    "instrumentos_musicais": "乐器",
    "moveis_sala": "客厅家具",
    "construcao_ferramentas_iluminacao": "照明工具",
    "industria_comercio_e_negocios": "工业商业",
    "alimentos": "食品",
    "artes": "艺术",
    "moveis_quarto": "卧室家具",
    "livros_interesse_geral": "大众读物",
    "construcao_ferramentas_seguranca": "安全防护工具",
    "fashion_underwear_e_moda_praia": "内衣泳装",
    "fashion_esporte": "运动服饰",
    "sinalizacao_e_seguranca": "安防用品",
    "pcs": "电脑整机",
    "artigos_de_natal": "圣诞用品",
    "fashion_roupa_feminina": "女装",
    "eletrodomesticos_2": "家用电器(2)",
    "livros_importados": "进口书籍",
    "bebidas": "饮品",
    "cine_foto": "摄影摄像",
    "la_cuisine": "厨具",
    "musica": "音乐",
    "casa_conforto_2": "家居舒适(2)",
    "portateis_casa_forno_e_cafe": "厨房小家电(烤箱/咖啡机)",
    "cds_dvds_musicais": "CD/DVD音像",
    "dvds_blu_ray": "DVD蓝光",
    "flores": "鲜花",
    "artes_e_artesanato": "手工艺品",
    "fraldas_higiene": "纸尿裤护理",
    "fashion_roupa_infanto_juvenil": "童装",
    "seguros_e_servicos": "保险服务",
    # 两个在 products 表中出现但 translation 表没有的类目
    "pc_gamer": "游戏电脑",
    "portateis_cozinha_e_preparadores_de_alimentos": "厨房料理小家电",
}

# 巴西 27 个州（含联邦区）：州代码 -> 中文
STATE_ZH = {
    "AC": "阿克里州", "AL": "阿拉戈斯州", "AP": "阿马帕州", "AM": "亚马逊州",
    "BA": "巴伊亚州", "CE": "塞阿拉州", "DF": "联邦区", "ES": "圣埃斯皮里图州",
    "GO": "戈亚斯州", "MA": "马拉尼昂州", "MT": "马托格罗索州", "MS": "南马托格罗索州",
    "MG": "米纳斯吉拉斯州", "PA": "帕拉州", "PB": "帕拉伊巴州", "PR": "巴拉那州",
    "PE": "伯南布哥州", "PI": "皮奥伊州", "RJ": "里约热内卢州", "RN": "北里奥格兰德州",
    "RS": "南里奥格兰德州", "RO": "朗多尼亚州", "RR": "罗赖马州", "SC": "圣卡塔琳娜州",
    "SP": "圣保罗州", "SE": "塞尔希培州", "TO": "托坎廷斯州",
}

# 支付方式 -> 中文
PAYMENT_ZH = {
    "credit_card": "信用卡",
    "boleto": "银行票据",
    "voucher": "优惠券",
    "debit_card": "借记卡",
    "not_defined": "未定义",
}


def to_zh(cat, fallback=""):
    """类目名转中文，未知类目回退到给定值或原始名。"""
    if isinstance(cat, str) and cat in CATEGORY_ZH:
        return CATEGORY_ZH[cat]
    return fallback or (cat if isinstance(cat, str) else "其他")


def state_zh(code):
    if isinstance(code, str) and code in STATE_ZH:
        return STATE_ZH[code]
    return code


def payment_zh(p):
    if isinstance(p, str) and p in PAYMENT_ZH:
        return PAYMENT_ZH[p]
    return p
