class ProductDao:
    def get_products(self, product_info, session):
        """ 상품 리스트 표출

        쿼리 파라미터에 따른 필터링된 상품 리스트를 전달합니다.

        args:
            product_info: 필터링을 위한 상품 정보
            session: 데이터베이스 session 객체

        returns :
            200: 필터링된 상품 리스트

        Authors:
            고지원

        History:
            2020-10-01 (고지원): 초기 생성
        """
        filter_query = """
            SELECT 
                p.id, 
                p_info.main_img, 
                p_info.name, 
                p_info.price, 
                p_info.sales_amount, 
                p_info.discount_rate, 
                p_info.discount_price, 
                p_info.created_at,
                p_info.seller_id,
                p_info.product_code,
                p_info.is_on_sale,
                p_info.is_displayed,
                p_info.is_promotion,
                s_info.korean_name,
                s_attr.attribution_name
            FROM products AS p
            
            # 상품 정보 조인
            INNER JOIN product_info AS p_info ON p.id = p_info.product_id

            # 셀러 정보 조인 
            INNER JOIN sellers AS s ON p_info.seller_id = s.id
            INNER JOIN seller_info AS s_info ON s_info.seller_id = s.id
            INNER JOIN seller_attributes AS s_attr ON s_attr.id = s_info.seller_attribute_id

            WHERE p_info.is_deleted = 0 
            AND p.is_deleted = 0 
            """

        # 조회 기간 시작
        if product_info.get('period_start', None):
            filter_query += " AND p_info.created_at >= :period_start"

        # 조회 기간 끝
        if product_info.get('period_end', None):
            filter_query += " AND p_info.created_at <= :period_end"

        # 진열 여부
        if product_info.get('is_displayed', None):
            filter_query += " AND p_info.is_displayed = :is_displayed"

        # 할인 여부
        if product_info.get('is_promotion', None):
            filter_query += " AND p_info.is_promotion = :is_promotion"

        # 판매 여부
        if product_info.get('is_on_sale', None):
            filter_query += " AND p_info.is_on_sale = :is_on_sale"

        # 셀러 속성
        if product_info.get('seller_attribute', None):
            filter_query += " AND s_attr.id = :seller_attribute"

        # 상품 검색: 상품명
        if product_info.get('select', None) == 0:
            # 검색어를 formatting 하여 LIKE 절에 사용
            q = product_info['q']
            product_info['q'] = f'%{q}%'

            filter_query += " AND p_info.name LIKE :q"

        # 상품 검색: 상품 번호
        elif product_info.get('select', None) == 1:
            q = product_info['q']
            product_info['q'] = f'%{q}%'

            filter_query += " AND p_info.product_id = :q"

        # 상품 검색: 상품 코드
        elif product_info.get('select', None) == 2:
            q = product_info['q']
            product_info['q'] = f'%{q}%'

            filter_query += " AND p_info.product_code = :q"

        # 셀러명 검색
        if product_info.get('seller_name', None):
            # 셀러명 검색어를 formatting 하여 LIKE 절에 사용
            name = product_info['seller_name']
            product_info['seller_name'] = f'%{name}%'

            filter_query += " AND s_info.korean_name LIKE :name"

        # pagination
        if product_info.get('limit', None):
            filter_query += " LIMIT :limit"

        # pagination
        if product_info.get('offset', None):
            filter_query += " OFFSET :offset"

        row = session.execute(filter_query, product_info)

        return row

    def get_product(self, product_id, session):
        """ 상품 상세 데이터 전달

        args:
            product_id: 상품 pk
            session: 데이터베이스 session 객체

        returns :
            200: 상품 상세 정보

        Authors:
            고지원

        History:
            2020-10-01 (고지원): 초기 생성
        """
        product_info = session.execute(("""
            SELECT 
                p.id AS p_id, 
                p_info.id AS p_info_id,
                p_info.product_code AS p_code,
                p_info.price, 
                p_info.is_on_sale,
                p_info.is_displayed,
                p_info.name,
                p_info.simple_description,
                p_info.detail_description,
                p_info.discount_rate, 
                p_info.discount_price,
                p_info.discount_start_date,
                p_info.discount_end_date,
                p_info.is_definite,
                p_info.min_unit,
                p_info.max_unit,
                p_info.sales_amount, 
                p_info.seller_id,
                f_cat.first_category_name,
                s_cat.second_category_name
            FROM products AS p 
            
            # 상품 정보 조인 
            INNER JOIN product_info AS p_info ON p_info.product_id = p.id
            
            # 카테고리 정보 조인 
            INNER JOIN first_categories AS f_cat ON f_cat.id = p_info.first_category_id
            INNER JOIN second_categories AS s_cat ON s_cat.id = p_info.second_category_id
            
            WHERE p_info.product_id = :product_id
            ORDER BY p_info.created_at DESC 
            LIMIT 1
        """), {'product_id' : product_id}).fetchone()

        # 이미지
        images = session.execute(("""
            SELECT 
                id, 
                URL
            FROM product_images
            WHERE product_info_id = :product_info_id
            ORDER BY ordering 
        """), {'product_info_id' : product_info.p_info_id})

        # 딕셔너리로 형변환
        product_info = dict(product_info)

        # 이미지 리스트를 images 키에 저장
        image_list = [{
            "id": image.id, "image_url": image.URL
        } for image in images]
        product_info['images'] = image_list

        return product_info