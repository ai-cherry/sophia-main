"""
Sophia AI - Snowflake Infrastructure as Code
This module defines Snowflake resources using Pulumi with enhanced support for
Gong, HubSpot, Slack, and Salesforce data integration
"""

import pulumi
import pulumi_snowflake as snowflake
from pulumi import Config

# Load configuration
config = Config()
env = config.require("environment")  # development, staging, or production

# Define environment-specific configurations
warehouse_sizes = {
    "development": "X-SMALL",
    "staging": "MEDIUM",
    "production": "LARGE"
}

database_names = {
    "development": "SOPHIA_DEV",
    "staging": "SOPHIA_STAGING",
    "production": "SOPHIA_PROD"
}

# Create a Snowflake warehouse
warehouse = snowflake.Warehouse("sophia_warehouse",
    name=f"SOPHIA_{env.upper()}_WH",
    warehouse_size=warehouse_sizes.get(env, "X-SMALL"),
    auto_suspend=60,
    auto_resume=True,
    initially_suspended=True
)

# Create a Snowflake database
database = snowflake.Database("sophia_database",
    name=database_names.get(env, f"SOPHIA_{env.upper()}")
)

# Create the main Sophia schema
main_schema = snowflake.Schema("sophia_schema",
    name="SOPHIA_MAIN",
    database=database.name
)

# Create integration-specific schemas
gong_schema = snowflake.Schema("gong_schema",
    name="GONG_DATA",
    database=database.name
)

hubspot_schema = snowflake.Schema("hubspot_schema",
    name="HUBSPOT_DATA",
    database=database.name
)

slack_schema = snowflake.Schema("slack_schema",
    name="SLACK_DATA",
    database=database.name
)

salesforce_schema = snowflake.Schema("salesforce_schema",
    name="SALESFORCE_DATA",
    database=database.name
)

# Create a unified analytics schema
analytics_schema = snowflake.Schema("analytics_schema",
    name="ANALYTICS",
    database=database.name
)

# Create a Snowflake role
role = snowflake.Role("sophia_role",
    name=f"SOPHIA_{env.upper()}_ROLE"
)

# Grant privileges to the role
warehouse_grant = snowflake.WarehouseGrant("sophia_warehouse_grant",
    warehouse_name=warehouse.name,
    privilege="USAGE",
    roles=[role.name]
)

database_grant = snowflake.DatabaseGrant("sophia_database_grant",
    database_name=database.name,
    privilege="USAGE",
    roles=[role.name]
)

# Grant privileges to all schemas
main_schema_grant = snowflake.SchemaGrant("main_schema_grant",
    database_name=database.name,
    schema_name=main_schema.name,
    privilege="USAGE",
    roles=[role.name]
)

gong_schema_grant = snowflake.SchemaGrant("gong_schema_grant",
    database_name=database.name,
    schema_name=gong_schema.name,
    privilege="USAGE",
    roles=[role.name]
)

hubspot_schema_grant = snowflake.SchemaGrant("hubspot_schema_grant",
    database_name=database.name,
    schema_name=hubspot_schema.name,
    privilege="USAGE",
    roles=[role.name]
)

slack_schema_grant = snowflake.SchemaGrant("slack_schema_grant",
    database_name=database.name,
    schema_name=slack_schema.name,
    privilege="USAGE",
    roles=[role.name]
)

salesforce_schema_grant = snowflake.SchemaGrant("salesforce_schema_grant",
    database_name=database.name,
    schema_name=salesforce_schema.name,
    privilege="USAGE",
    roles=[role.name]
)

analytics_schema_grant = snowflake.SchemaGrant("analytics_schema_grant",
    database_name=database.name,
    schema_name=analytics_schema.name,
    privilege="USAGE",
    roles=[role.name]
)

# Define Gong tables
gong_tables = {
    "calls": {
        "columns": [
            {"name": "call_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "title", "type": "VARCHAR(255)"},
            {"name": "start_time", "type": "TIMESTAMP_NTZ"},
            {"name": "end_time", "type": "TIMESTAMP_NTZ"},
            {"name": "duration_seconds", "type": "INTEGER"},
            {"name": "recording_url", "type": "VARCHAR(1024)"},
            {"name": "content_url", "type": "VARCHAR(1024)"},
            {"name": "media_url", "type": "VARCHAR(1024)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "participants": {
        "columns": [
            {"name": "participant_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "call_id", "type": "VARCHAR(255)", "foreign_key": "calls(call_id)"},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "email", "type": "VARCHAR(255)"},
            {"name": "role", "type": "VARCHAR(50)"},
            {"name": "speaking_time_seconds", "type": "INTEGER"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "transcripts": {
        "columns": [
            {"name": "transcript_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "call_id", "type": "VARCHAR(255)", "foreign_key": "calls(call_id)"},
            {"name": "participant_id", "type": "VARCHAR(255)", "foreign_key": "participants(participant_id)"},
            {"name": "start_time", "type": "TIMESTAMP_NTZ"},
            {"name": "end_time", "type": "TIMESTAMP_NTZ"},
            {"name": "text", "type": "TEXT"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "topics": {
        "columns": [
            {"name": "topic_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "call_id", "type": "VARCHAR(255)", "foreign_key": "calls(call_id)"},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "start_time", "type": "TIMESTAMP_NTZ"},
            {"name": "end_time", "type": "TIMESTAMP_NTZ"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "trackers": {
        "columns": [
            {"name": "tracker_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "call_id", "type": "VARCHAR(255)", "foreign_key": "calls(call_id)"},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "value", "type": "VARCHAR(255)"},
            {"name": "start_time", "type": "TIMESTAMP_NTZ"},
            {"name": "end_time", "type": "TIMESTAMP_NTZ"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    }
}

# Define HubSpot tables
hubspot_tables = {
    "contacts": {
        "columns": [
            {"name": "contact_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "email", "type": "VARCHAR(255)"},
            {"name": "first_name", "type": "VARCHAR(255)"},
            {"name": "last_name", "type": "VARCHAR(255)"},
            {"name": "phone", "type": "VARCHAR(50)"},
            {"name": "company", "type": "VARCHAR(255)"},
            {"name": "job_title", "type": "VARCHAR(255)"},
            {"name": "lifecycle_stage", "type": "VARCHAR(50)"},
            {"name": "lead_status", "type": "VARCHAR(50)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "companies": {
        "columns": [
            {"name": "company_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "domain", "type": "VARCHAR(255)"},
            {"name": "industry", "type": "VARCHAR(255)"},
            {"name": "annual_revenue", "type": "NUMBER(38,2)"},
            {"name": "employees", "type": "INTEGER"},
            {"name": "city", "type": "VARCHAR(255)"},
            {"name": "state", "type": "VARCHAR(255)"},
            {"name": "country", "type": "VARCHAR(255)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "deals": {
        "columns": [
            {"name": "deal_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "company_id", "type": "VARCHAR(255)", "foreign_key": "companies(company_id)"},
            {"name": "deal_name", "type": "VARCHAR(255)"},
            {"name": "amount", "type": "NUMBER(38,2)"},
            {"name": "deal_stage", "type": "VARCHAR(50)"},
            {"name": "close_date", "type": "DATE"},
            {"name": "pipeline", "type": "VARCHAR(50)"},
            {"name": "deal_type", "type": "VARCHAR(50)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    }
}

# Define Slack tables
slack_tables = {
    "channels": {
        "columns": [
            {"name": "channel_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "is_private", "type": "BOOLEAN"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "users": {
        "columns": [
            {"name": "user_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "real_name", "type": "VARCHAR(255)"},
            {"name": "email", "type": "VARCHAR(255)"},
            {"name": "is_admin", "type": "BOOLEAN"},
            {"name": "is_bot", "type": "BOOLEAN"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "messages": {
        "columns": [
            {"name": "message_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "channel_id", "type": "VARCHAR(255)", "foreign_key": "channels(channel_id)"},
            {"name": "user_id", "type": "VARCHAR(255)", "foreign_key": "users(user_id)"},
            {"name": "text", "type": "TEXT"},
            {"name": "ts", "type": "VARCHAR(50)"},
            {"name": "thread_ts", "type": "VARCHAR(50)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    }
}

# Define Salesforce tables
salesforce_tables = {
    "accounts": {
        "columns": [
            {"name": "account_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "type", "type": "VARCHAR(50)"},
            {"name": "industry", "type": "VARCHAR(255)"},
            {"name": "annual_revenue", "type": "NUMBER(38,2)"},
            {"name": "employees", "type": "INTEGER"},
            {"name": "billing_city", "type": "VARCHAR(255)"},
            {"name": "billing_state", "type": "VARCHAR(255)"},
            {"name": "billing_country", "type": "VARCHAR(255)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "contacts": {
        "columns": [
            {"name": "contact_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "account_id", "type": "VARCHAR(255)", "foreign_key": "accounts(account_id)"},
            {"name": "first_name", "type": "VARCHAR(255)"},
            {"name": "last_name", "type": "VARCHAR(255)"},
            {"name": "email", "type": "VARCHAR(255)"},
            {"name": "phone", "type": "VARCHAR(50)"},
            {"name": "title", "type": "VARCHAR(255)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    },
    "opportunities": {
        "columns": [
            {"name": "opportunity_id", "type": "VARCHAR(255)", "primary_key": True},
            {"name": "account_id", "type": "VARCHAR(255)", "foreign_key": "accounts(account_id)"},
            {"name": "name", "type": "VARCHAR(255)"},
            {"name": "stage", "type": "VARCHAR(50)"},
            {"name": "amount", "type": "NUMBER(38,2)"},
            {"name": "close_date", "type": "DATE"},
            {"name": "probability", "type": "NUMBER(5,2)"},
            {"name": "type", "type": "VARCHAR(50)"},
            {"name": "created_at", "type": "TIMESTAMP_NTZ"},
            {"name": "updated_at", "type": "TIMESTAMP_NTZ"}
        ]
    }
}

# Define analytics views
analytics_views = {
    "customer_360": {
        "query": f"""
        SELECT 
            sf.accounts.account_id,
            sf.accounts.name AS account_name,
            sf.accounts.industry,
            sf.accounts.annual_revenue,
            sf.accounts.employees,
            hs.companies.company_id AS hubspot_company_id,
            hs.companies.domain AS hubspot_domain,
            COUNT(DISTINCT sf.opportunities.opportunity_id) AS opportunity_count,
            SUM(sf.opportunities.amount) AS total_opportunity_amount,
            COUNT(DISTINCT g.calls.call_id) AS call_count,
            SUM(g.calls.duration_seconds) / 60 AS total_call_minutes,
            COUNT(DISTINCT sl.messages.message_id) AS slack_message_count
        FROM {database_names.get(env, f"SOPHIA_{env.upper()}")}.SALESFORCE_DATA.accounts sf.accounts
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.SALESFORCE_DATA.opportunities sf.opportunities
            ON sf.accounts.account_id = sf.opportunities.account_id
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.HUBSPOT_DATA.companies hs.companies
            ON sf.accounts.name = hs.companies.name
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.GONG_DATA.calls g.calls
            ON sf.accounts.name = g.calls.title
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.SLACK_DATA.channels sl.channels
            ON sf.accounts.name = sl.channels.name
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.SLACK_DATA.messages sl.messages
            ON sl.channels.channel_id = sl.messages.channel_id
        GROUP BY 
            sf.accounts.account_id,
            sf.accounts.name,
            sf.accounts.industry,
            sf.accounts.annual_revenue,
            sf.accounts.employees,
            hs.companies.company_id,
            hs.companies.domain
        """
    },
    "sales_performance": {
        "query": f"""
        SELECT 
            sf.opportunities.stage,
            DATE_TRUNC('month', sf.opportunities.close_date) AS close_month,
            COUNT(DISTINCT sf.opportunities.opportunity_id) AS opportunity_count,
            SUM(sf.opportunities.amount) AS total_amount,
            AVG(sf.opportunities.amount) AS avg_amount,
            AVG(sf.opportunities.probability) AS avg_probability,
            COUNT(DISTINCT g.calls.call_id) AS call_count,
            SUM(g.calls.duration_seconds) / 60 AS total_call_minutes,
            COUNT(DISTINCT g.calls.call_id) / COUNT(DISTINCT sf.opportunities.opportunity_id) AS calls_per_opportunity
        FROM {database_names.get(env, f"SOPHIA_{env.upper()}")}.SALESFORCE_DATA.opportunities sf.opportunities
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.SALESFORCE_DATA.accounts sf.accounts
            ON sf.opportunities.account_id = sf.accounts.account_id
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.GONG_DATA.calls g.calls
            ON sf.accounts.name = g.calls.title
        GROUP BY 
            sf.opportunities.stage,
            close_month
        ORDER BY 
            close_month,
            sf.opportunities.stage
        """
    },
    "call_analytics": {
        "query": f"""
        SELECT 
            DATE_TRUNC('day', g.calls.start_time) AS call_date,
            COUNT(DISTINCT g.calls.call_id) AS call_count,
            SUM(g.calls.duration_seconds) / 60 AS total_call_minutes,
            AVG(g.calls.duration_seconds) / 60 AS avg_call_minutes,
            COUNT(DISTINCT g.participants.participant_id) AS participant_count,
            COUNT(DISTINCT g.topics.topic_id) AS topic_count,
            COUNT(DISTINCT g.trackers.tracker_id) AS tracker_count
        FROM {database_names.get(env, f"SOPHIA_{env.upper()}")}.GONG_DATA.calls g.calls
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.GONG_DATA.participants g.participants
            ON g.calls.call_id = g.participants.call_id
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.GONG_DATA.topics g.topics
            ON g.calls.call_id = g.topics.call_id
        LEFT JOIN {database_names.get(env, f"SOPHIA_{env.upper()}")}.GONG_DATA.trackers g.trackers
            ON g.calls.call_id = g.trackers.call_id
        GROUP BY 
            call_date
        ORDER BY 
            call_date
        """
    }
}

# Create tables for each schema
gong_table_resources = {}
for table_name, table_config in gong_tables.items():
    columns_sql = []
    for column in table_config["columns"]:
        column_sql = f"{column['name']} {column['type']}"
        if column.get("primary_key"):
            column_sql += " PRIMARY KEY"
        columns_sql.append(column_sql)
    
    foreign_keys = []
    for column in table_config["columns"]:
        if column.get("foreign_key"):
            foreign_keys.append(f"FOREIGN KEY ({column['name']}) REFERENCES {column['foreign_key']}")
    
    if foreign_keys:
        columns_sql.extend(foreign_keys)
    
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {database.name}.{gong_schema.name}.{table_name} ({', '.join(columns_sql)})"
    
    gong_table_resources[table_name] = snowflake.SqlStatement(f"gong_{table_name}_table",
        database=database.name,
        schema=gong_schema.name,
        statement=create_table_sql
    )

hubspot_table_resources = {}
for table_name, table_config in hubspot_tables.items():
    columns_sql = []
    for column in table_config["columns"]:
        column_sql = f"{column['name']} {column['type']}"
        if column.get("primary_key"):
            column_sql += " PRIMARY KEY"
        columns_sql.append(column_sql)
    
    foreign_keys = []
    for column in table_config["columns"]:
        if column.get("foreign_key"):
            foreign_keys.append(f"FOREIGN KEY ({column['name']}) REFERENCES {column['foreign_key']}")
    
    if foreign_keys:
        columns_sql.extend(foreign_keys)
    
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {database.name}.{hubspot_schema.name}.{table_name} ({', '.join(columns_sql)})"
    
    hubspot_table_resources[table_name] = snowflake.SqlStatement(f"hubspot_{table_name}_table",
        database=database.name,
        schema=hubspot_schema.name,
        statement=create_table_sql
    )

slack_table_resources = {}
for table_name, table_config in slack_tables.items():
    columns_sql = []
    for column in table_config["columns"]:
        column_sql = f"{column['name']} {column['type']}"
        if column.get("primary_key"):
            column_sql += " PRIMARY KEY"
        columns_sql.append(column_sql)
    
    foreign_keys = []
    for column in table_config["columns"]:
        if column.get("foreign_key"):
            foreign_keys.append(f"FOREIGN KEY ({column['name']}) REFERENCES {column['foreign_key']}")
    
    if foreign_keys:
        columns_sql.extend(foreign_keys)
    
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {database.name}.{slack_schema.name}.{table_name} ({', '.join(columns_sql)})"
    
    slack_table_resources[table_name] = snowflake.SqlStatement(f"slack_{table_name}_table",
        database=database.name,
        schema=slack_schema.name,
        statement=create_table_sql
    )

salesforce_table_resources = {}
for table_name, table_config in salesforce_tables.items():
    columns_sql = []
    for column in table_config["columns"]:
        column_sql = f"{column['name']} {column['type']}"
        if column.get("primary_key"):
            column_sql += " PRIMARY KEY"
        columns_sql.append(column_sql)
    
    foreign_keys = []
    for column in table_config["columns"]:
        if column.get("foreign_key"):
            foreign_keys.append(f"FOREIGN KEY ({column['name']}) REFERENCES {column['foreign_key']}")
    
    if foreign_keys:
        columns_sql.extend(foreign_keys)
    
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {database.name}.{salesforce_schema.name}.{table_name} ({', '.join(columns_sql)})"
    
    salesforce_table_resources[table_name] = snowflake.SqlStatement(f"salesforce_{table_name}_table",
        database=database.name,
        schema=salesforce_schema.name,
        statement=create_table_sql
    )

# Create analytics views
analytics_view_resources = {}
for view_name, view_config in analytics_views.items():
    create_view_sql = f"CREATE OR REPLACE VIEW {database.name}.{analytics_schema.name}.{view_name} AS {view_config['query']}"
    
    analytics_view_resources[view_name] = snowflake.SqlStatement(f"analytics_{view_name}_view",
        database=database.name,
        schema=analytics_schema.name,
        statement=create_view_sql
    )

# Create a Snowflake task to refresh analytics views
refresh_analytics_task = snowflake.Task("refresh_analytics_task",
    name="REFRESH_ANALYTICS_VIEWS",
    database=database.name,
    schema=analytics_schema.name,
    warehouse=warehouse.name,
    schedule="USING CRON 0 */6 * * * UTC",
    sql_statement=f"""
    REFRESH MATERIALIZED VIEW {database.name}.{analytics_schema.name}.customer_360;
    REFRESH MATERIALIZED VIEW {database.name}.{analytics_schema.name}.sales_performance;
    REFRESH MATERIALIZED VIEW {database.name}.{analytics_schema.name}.call_analytics;
    """
)

# Export outputs
pulumi.export("warehouse_name", warehouse.name)
pulumi.export("database_name", database.name)
pulumi.export("main_schema_name", main_schema.name)
pulumi.export("gong_schema_name", gong_schema.name)
pulumi.export("hubspot_schema_name", hubspot_schema.name)
pulumi.export("slack_schema_name", slack_schema.name)
pulumi.export("salesforce_schema_name", salesforce_schema.name)
pulumi.export("analytics_schema_name", analytics_schema.name)
pulumi.export("role_name", role.name)
pulumi.export("gong_tables", list(gong_tables.keys()))
pulumi.export("hubspot_tables", list(hubspot_tables.keys()))
pulumi.export("slack_tables", list(slack_tables.keys()))
pulumi.export("salesforce_tables", list(salesforce_tables.keys()))
pulumi.export("analytics_views", list(analytics_views.keys()))
