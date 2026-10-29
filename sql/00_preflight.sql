-- Read-only. Execute after the local server is running and authentication succeeds.
SELECT VERSION() AS ServerVersion, @@port AS ServerPort, CURRENT_USER() AS AuthenticatedAccount;
-- Only create retail_sales_analysis if this is zero. Do not overwrite an existing database.
SELECT COUNT(*) AS database_exists FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'retail_sales_analysis';
