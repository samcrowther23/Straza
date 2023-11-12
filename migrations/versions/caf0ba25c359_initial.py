"""Initial

Revision ID: caf0ba25c359
Revises: 
Create Date: 2023-11-09 15:42:14.204790

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'caf0ba25c359'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('table')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('username')

    op.drop_table('users')
    with op.batch_alter_table('runs', schema=None) as batch_op:
        batch_op.alter_column('zone_2_time',
               existing_type=mysql.FLOAT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('zone_3_time',
               existing_type=mysql.FLOAT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('zone_4_time',
               existing_type=mysql.FLOAT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('zone_5_time',
               existing_type=mysql.FLOAT(),
               type_=sa.Integer(),
               existing_nullable=True)
        batch_op.alter_column('total_time',
               existing_type=mysql.FLOAT(),
               type_=sa.Integer(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('runs', schema=None) as batch_op:
        batch_op.alter_column('total_time',
               existing_type=sa.Integer(),
               type_=mysql.FLOAT(),
               existing_nullable=True)
        batch_op.alter_column('zone_5_time',
               existing_type=sa.Integer(),
               type_=mysql.FLOAT(),
               existing_nullable=True)
        batch_op.alter_column('zone_4_time',
               existing_type=sa.Integer(),
               type_=mysql.FLOAT(),
               existing_nullable=True)
        batch_op.alter_column('zone_3_time',
               existing_type=sa.Integer(),
               type_=mysql.FLOAT(),
               existing_nullable=True)
        batch_op.alter_column('zone_2_time',
               existing_type=sa.Integer(),
               type_=mysql.FLOAT(),
               existing_nullable=True)

    op.create_table('users',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('username', mysql.VARCHAR(length=50), nullable=True),
    sa.Column('password', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('profile_picture_path', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('table_data', mysql.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index('username', ['username'], unique=False)

    op.create_table('table',
    sa.Column('user_id', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('table_data', mysql.JSON(), nullable=True),
    sa.Column('table_colour', mysql.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='table_ibfk_1'),
    sa.PrimaryKeyConstraint('user_id'),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###