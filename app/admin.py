from app.models.database import get_connection

space_title = input('Enter title space: ')
space_location = input('Enter location space: ')
space_capacity = input('Enter capacity space: ')
space_image = input('Enter image space: ')
space_description = input('Enter space description: ')
space_type = input('Enter space type: ')

conn = get_connection()
cursor = conn.cursor()
cursor.execute('''
                INSERT INTO spaces (space_title, space_location, space_capacity, space_image, space_description, space_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (space_title, space_location, space_capacity, space_image, space_description, space_type))
conn.commit()