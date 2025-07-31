from app.models.category import CategoryCreate, CategoryOut, CategoryUpdate, CategoryFilters
from fastapi import HTTPException

class CategoryService:
    def __init__(self, db):
        self.db = db

    async def create_category(self, category: CategoryCreate, user_id: int) -> CategoryOut:
        cursor = self.db.cursor()
        cursor.execute(
            "INSERT INTO categories (name, user_id, color) VALUES (%s, %s, %s) RETURNING id, name, user_id, color",
            (category.name, user_id, category.color)
        )
        self.db.commit()
        category_data = cursor.fetchone()
        return CategoryOut(**category_data)


    async def get_user_categories(self, filters: CategoryFilters, user_id: int) -> list[CategoryOut]:
        conditions = ["user_id = %s"]
        params = [user_id]

        filters_map = {
            "name": ("name LIKE %s", f"%{filters.name}%"),
            "color": ("color = %s", filters.color),
        }

        for field, (condition, value) in filters_map.items():
            if getattr(filters, field) is not None:
                conditions.append(condition)
                params.append(value)

        query = f"""
            SELECT id, name, user_id, color
            FROM categories
            WHERE {' AND '.join(conditions)}
        """

        cursor = self.db.cursor()
        cursor.execute(query, tuple(params))
        categories = cursor.fetchall()
        return [CategoryOut(**cat) for cat in categories]

    async def get_category(self, category_id: int, user_id: int) -> CategoryOut:
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT id, name, color
            FROM categories
            WHERE id = %s AND user_id = %s
            """,
            (category_id, user_id)
        )
        category = cursor.fetchone()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or not owned by user")
        return CategoryOut(**category)

    async def update_category(self, category_id: int, category_data: CategoryUpdate, user_id: int,
                              is_admin: bool = False) -> CategoryOut:
        cursor = self.db.cursor()

        if not is_admin:
            cursor.execute("SELECT id FROM categories WHERE id = %s AND user_id = %s", (category_id, user_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Category not found or not owned by user")
        else:
            cursor.execute("SELECT id FROM categories WHERE id = %s", (category_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Category not found")

        updates = {k: v for k, v in category_data.dict(exclude_unset=True).items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
        where_clause = "id = %s" if is_admin else "id = %s AND user_id = %s"

        set_values = list(updates.values())
        where_values = [category_id] if is_admin else [category_id, user_id]
        values = set_values + where_values

        cursor.execute(
            f"UPDATE categories SET {set_clause} "
            f"WHERE {where_clause} RETURNING id, name, user_id, color",
            values
        )
        self.db.commit()
        updated_category = cursor.fetchone()
        return CategoryOut(**updated_category)


    async def delete_category(self, category_id: int, user_id: int, is_admin: bool = False):
        cursor = self.db.cursor()

        where_clause = "id = %s" if is_admin else "id = %s AND user_id = %s"
        values = [category_id] if is_admin else [category_id, user_id]

        cursor.execute(f"SELECT id FROM categories WHERE {where_clause}", values)
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Category not found or not owned by user")

        cursor.execute(f"DELETE FROM categories WHERE {where_clause}", values)
        self.db.commit()