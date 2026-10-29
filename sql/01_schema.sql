-- Created and validated on MariaDB 10.4.32; see reports/sql_reconciliation.md.
-- Fresh-server setup only: do not rerun against the populated project database.
-- First run sql/00_preflight.sql and confirm database_exists = 0.
-- If this database already exists, STOP and preserve it; do not run this file.
-- No IF NOT EXISTS: an existing name must fail. Never use mysql --force.
CREATE DATABASE retail_sales_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
USE retail_sales_analysis;
CREATE TABLE sales (
 SourceRow BIGINT NOT NULL PRIMARY KEY,
 InvoiceNo VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
 StockCode VARCHAR(64) COLLATE utf8mb4_bin NOT NULL,
 Description VARCHAR(512) COLLATE utf8mb4_bin NULL,
 Quantity BIGINT NOT NULL,
 InvoiceDate DATETIME NOT NULL,
 UnitPrice DECIMAL(20,6) NOT NULL,
 CustomerID VARCHAR(64) COLLATE utf8mb4_bin NULL,
 Country VARCHAR(128) COLLATE utf8mb4_bin NULL,
 LineSalesPence BIGINT NOT NULL,
 LineSalesGBP DECIMAL(20,2) NOT NULL,
 INDEX ix_invoice (InvoiceNo), INDEX ix_customer (CustomerID),
 INDEX ix_date (InvoiceDate), INDEX ix_stock (StockCode)
);
CREATE TABLE analysis_metadata (
 Id INT PRIMARY KEY,
 CoverageStart DATETIME NOT NULL,
 CoverageEnd DATETIME NOT NULL,
 SourceCSV_SHA256 CHAR(64) NOT NULL
);
