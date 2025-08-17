-- RMA Database Schema

-- Enhanced RMA Database Schema with Improvements
-- Author: Stephen Green

-- Create database and use it
CREATE DATABASE IF NOT EXISTS enhanced_rma_system;
USE enhanced_rma_system;

-- Enable foreign key constraints
SET FOREIGN_KEY_CHECKS = 1;

-- 1. CUSTOMERS TABLE (Enhanced with constraints)
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(25) NOT NULL,
    LastName VARCHAR(25) NOT NULL,
    Street VARCHAR(50) NOT NULL,
    City VARCHAR(50) NOT NULL,
    State VARCHAR(2) NOT NULL CHECK (LENGTH(State) = 2), -- Ensures state codes are exactly 2 characters
    ZipCode VARCHAR(10) NOT NULL CHECK (ZipCode REGEXP '^[0-9]{5}(-[0-9]{4})?$'), -- US ZIP code format
    Telephone VARCHAR(15) NOT NULL CHECK (Telephone REGEXP '^[0-9\-\+\(\) ]+$'), -- Basic phone validation
    Email VARCHAR(100) UNIQUE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. ORDERS TABLE (Enhanced - header level only)
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID INT NOT NULL,
    OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    OrderStatus ENUM('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled') DEFAULT 'Pending',
    TotalAmount DECIMAL(10,2) DEFAULT 0.00,
    ShippingAddress VARCHAR(200),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE RESTRICT
);

-- 3. NEW: ORDER_DETAILS TABLE (Supports multi-item orders)
CREATE TABLE OrderDetails (
    OrderDetailID INT PRIMARY KEY AUTO_INCREMENT,
    OrderID INT NOT NULL,
    SKU VARCHAR(20) NOT NULL,
    ProductDescription VARCHAR(100) NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    UnitPrice DECIMAL(8,2) NOT NULL CHECK (UnitPrice >= 0),
    LineTotal DECIMAL(10,2) GENERATED ALWAYS AS (Quantity * UnitPrice) STORED,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE CASCADE
);

-- 4. PRODUCTS TABLE (New - for better SKU management)
CREATE TABLE Products (
    SKU VARCHAR(20) PRIMARY KEY,
    ProductName VARCHAR(100) NOT NULL,
    Category VARCHAR(50),
    UnitPrice DECIMAL(8,2) NOT NULL CHECK (UnitPrice >= 0),
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. RMA TABLE (Enhanced with better constraints and status tracking)
CREATE TABLE RMA (
    RMAID INT PRIMARY KEY AUTO_INCREMENT,
    OrderID INT NOT NULL,
    OrderDetailID INT,
    CustomerID INT NOT NULL,
    RMADate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Reason ENUM('Defective', 'Wrong Item', 'Not as Described', 'Damaged in Shipping', 'Customer Error', 'Other') NOT NULL,
    ReasonDetails VARCHAR(500),
    Status ENUM('Requested', 'Approved', 'Rejected', 'In Transit', 'Received', 'Processed', 'Refunded', 'Exchanged') DEFAULT 'Requested',
    RequestedAction ENUM('Refund', 'Exchange', 'Repair') NOT NULL,
    ApprovedBy INT,
    Resolution VARCHAR(500),
    RefundAmount DECIMAL(10,2),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (OrderID) REFERENCES Orders(OrderID) ON DELETE RESTRICT,
    FOREIGN KEY (OrderDetailID) REFERENCES OrderDetails(OrderDetailID) ON DELETE RESTRICT,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE RESTRICT
);

-- 6. RMA_STATUS_HISTORY TABLE (Tracks status changes)
CREATE TABLE RMAStatusHistory (
    HistoryID INT PRIMARY KEY AUTO_INCREMENT,
    RMAID INT NOT NULL,
    OldStatus VARCHAR(20),
    NewStatus VARCHAR(20) NOT NULL,
    ChangedBy VARCHAR(50),
    ChangeReason VARCHAR(200),
    ChangeDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (RMAID) REFERENCES RMA(RMAID) ON DELETE CASCADE
);

-- 7. USERS TABLE (For role-based access control simulation)
CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) UNIQUE NOT NULL,
    PasswordHash VARCHAR(255) NOT NULL, -- In real implementation, store hashed passwords
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Role ENUM('Admin', 'Manager', 'Customer_Service', 'Warehouse', 'Readonly') NOT NULL,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastLogin TIMESTAMP NULL
);

-- Create indexes for better performance
CREATE INDEX idx_customers_state ON Customers(State);
CREATE INDEX idx_orders_customer ON Orders(CustomerID);
CREATE INDEX idx_orders_date ON Orders(OrderDate);
CREATE INDEX idx_orderdetails_sku ON OrderDetails(SKU);
CREATE INDEX idx_rma_customer ON RMA(CustomerID);
CREATE INDEX idx_rma_date ON RMA(RMADate);
CREATE INDEX idx_rma_status ON RMA(Status);
CREATE INDEX idx_rma_reason ON RMA(Reason);

-- RMA Stored Procedures

-- Enhanced RMA Database Stored Procedures
-- Implements core business logic with proper validation and logging
-- Author: Stephen Green

DELIMITER $$

-- 1. PROCEDURE: Create a new RMA with validation
CREATE PROCEDURE CreateRMA(
    IN p_OrderID INT,
    IN p_OrderDetailID INT,
    IN p_CustomerID INT,
    IN p_Reason VARCHAR(50),
    IN p_ReasonDetails VARCHAR(500),
    IN p_RequestedAction VARCHAR(20),
    IN p_CreatedBy VARCHAR(50),
    OUT p_RMAID INT,
    OUT p_Result VARCHAR(100)
)
BEGIN
    DECLARE v_OrderExists INT DEFAULT 0;
    DECLARE v_CustomerMatch INT DEFAULT 0;
    DECLARE v_OrderDetailExists INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_Result = 'Error: Transaction failed';
        SET p_RMAID = -1;
    END;

    START TRANSACTION;

    -- Validate order exists
    SELECT COUNT(*) INTO v_OrderExists 
    FROM Orders 
    WHERE OrderID = p_OrderID;

    IF v_OrderExists = 0 THEN
        SET p_Result = 'Error: Order does not exist';
        SET p_RMAID = -1;
        ROLLBACK;
    ELSE
        -- Validate customer matches order
        SELECT COUNT(*) INTO v_CustomerMatch 
        FROM Orders 
        WHERE OrderID = p_OrderID AND CustomerID = p_CustomerID;

        IF v_CustomerMatch = 0 THEN
            SET p_Result = 'Error: Customer does not match order';
            SET p_RMAID = -1;
            ROLLBACK;
        ELSE
            -- Validate order detail exists if provided
            IF p_OrderDetailID IS NOT NULL THEN
                SELECT COUNT(*) INTO v_OrderDetailExists 
                FROM OrderDetails 
                WHERE OrderDetailID = p_OrderDetailID AND OrderID = p_OrderID;

                IF v_OrderDetailExists = 0 THEN
                    SET p_Result = 'Error: Order detail does not exist for this order';
                    SET p_RMAID = -1;
                    ROLLBACK;
                END IF;
            END IF;

            -- If all validations pass, create RMA
            IF p_RMAID != -1 THEN
                INSERT INTO RMA (OrderID, OrderDetailID, CustomerID, Reason, ReasonDetails, RequestedAction)
                VALUES (p_OrderID, p_OrderDetailID, p_CustomerID, p_Reason, p_ReasonDetails, p_RequestedAction);

                SET p_RMAID = LAST_INSERT_ID();

                -- Log initial status
                INSERT INTO RMAStatusHistory (RMAID, OldStatus, NewStatus, ChangedBy, ChangeReason)
                VALUES (p_RMAID, NULL, 'Requested', p_CreatedBy, 'RMA created');

                SET p_Result = 'Success: RMA created successfully';
                COMMIT;
            END IF;
        END IF;
    END IF;
END$$

-- 2. PROCEDURE: Update RMA Status with history logging
CREATE PROCEDURE UpdateRMAStatus(
    IN p_RMAID INT,
    IN p_NewStatus VARCHAR(20),
    IN p_ChangedBy VARCHAR(50),
    IN p_ChangeReason VARCHAR(200),
    IN p_Resolution VARCHAR(500),
    IN p_RefundAmount DECIMAL(10,2),
    OUT p_Result VARCHAR(100)
)
BEGIN
    DECLARE v_OldStatus VARCHAR(20);
    DECLARE v_RMAExists INT DEFAULT 0;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_Result = 'Error: Transaction failed';
    END;

    START TRANSACTION;

    -- Check if RMA exists and get current status
    SELECT COUNT(*), MAX(Status) INTO v_RMAExists, v_OldStatus
    FROM RMA 
    WHERE RMAID = p_RMAID;

    IF v_RMAExists = 0 THEN
        SET p_Result = 'Error: RMA does not exist';
        ROLLBACK;
    ELSE
        -- Update RMA record
        UPDATE RMA 
        SET Status = p_NewStatus,
            Resolution = COALESCE(p_Resolution, Resolution),
            RefundAmount = COALESCE(p_RefundAmount, RefundAmount),
            UpdatedDate = CURRENT_TIMESTAMP
        WHERE RMAID = p_RMAID;

        -- Log status change
        INSERT INTO RMAStatusHistory (RMAID, OldStatus, NewStatus, ChangedBy, ChangeReason)
        VALUES (p_RMAID, v_OldStatus, p_NewStatus, p_ChangedBy, p_ChangeReason);

        SET p_Result = 'Success: RMA status updated successfully';
        COMMIT;
    END IF;
END$$

-- 3. PROCEDURE: Get RMA details with customer and order information
CREATE PROCEDURE GetRMADetails(
    IN p_RMAID INT
)
BEGIN
    SELECT 
        r.RMAID,
        r.RMADate,
        r.Reason,
        r.ReasonDetails,
        r.Status,
        r.RequestedAction,
        r.Resolution,
        r.RefundAmount,
        c.FirstName,
        c.LastName,
        c.Email,
        c.Telephone,
        o.OrderID,
        o.OrderDate,
        od.SKU,
        od.ProductDescription,
        od.Quantity,
        od.UnitPrice,
        od.LineTotal
    FROM RMA r
    JOIN Customers c ON r.CustomerID = c.CustomerID
    JOIN Orders o ON r.OrderID = o.OrderID
    LEFT JOIN OrderDetails od ON r.OrderDetailID = od.OrderDetailID
    WHERE r.RMAID = p_RMAID;
END$$

-- 4. PROCEDURE: Get return rates by SKU (normalized by sales volume)
CREATE PROCEDURE GetReturnRatesBySKU()
BEGIN
    SELECT 
        p.SKU,
        p.ProductName,
        p.Category,
        COALESCE(sales.TotalSold, 0) as TotalSold,
        COALESCE(returns.TotalReturns, 0) as TotalReturns,
        CASE 
            WHEN COALESCE(sales.TotalSold, 0) = 0 THEN 0
            ELSE ROUND((COALESCE(returns.TotalReturns, 0) / sales.TotalSold) * 100, 2)
        END as ReturnRatePercent
    FROM Products p
    LEFT JOIN (
        SELECT 
            od.SKU,
            SUM(od.Quantity) as TotalSold
        FROM OrderDetails od
        JOIN Orders o ON od.OrderID = o.OrderID
        WHERE o.OrderStatus = 'Delivered'
        GROUP BY od.SKU
    ) sales ON p.SKU = sales.SKU
    LEFT JOIN (
        SELECT 
            od.SKU,
            COUNT(*) as TotalReturns
        FROM RMA r
        JOIN OrderDetails od ON r.OrderDetailID = od.OrderDetailID
        GROUP BY od.SKU
    ) returns ON p.SKU = returns.SKU
    ORDER BY ReturnRatePercent DESC, TotalReturns DESC;
END$$

-- 5. PROCEDURE: Get return statistics by state (normalized)
CREATE PROCEDURE GetReturnStatsByState()
BEGIN
    SELECT 
        c.State,
        COUNT(DISTINCT o.OrderID) as TotalOrders,
        COUNT(r.RMAID) as TotalReturns,
        CASE 
            WHEN COUNT(DISTINCT o.OrderID) = 0 THEN 0
            ELSE ROUND((COUNT(r.RMAID) / COUNT(DISTINCT o.OrderID)) * 100, 2)
        END as ReturnRatePercent,
        SUM(COALESCE(r.RefundAmount, 0)) as TotalRefundAmount
    FROM Customers c
    LEFT JOIN Orders o ON c.CustomerID = o.CustomerID AND o.OrderStatus = 'Delivered'
    LEFT JOIN RMA r ON o.OrderID = r.OrderID
    GROUP BY c.State
    ORDER BY ReturnRatePercent DESC, TotalReturns DESC;
END$$

-- 6. PROCEDURE: Get RMA status history
CREATE PROCEDURE GetRMAStatusHistory(
    IN p_RMAID INT
)
BEGIN
    SELECT 
        h.HistoryID,
        h.OldStatus,
        h.NewStatus,
        h.ChangedBy,
        h.ChangeReason,
        h.ChangeDate
    FROM RMAStatusHistory h
    WHERE h.RMAID = p_RMAID
    ORDER BY h.ChangeDate DESC;
END$$

-- 7. PROCEDURE: Monthly RMA report
CREATE PROCEDURE GetMonthlyRMAReport(
    IN p_Year INT,
    IN p_Month INT
)
BEGIN
    SELECT 
        DATE(r.RMADate) as RMADay,
        COUNT(*) as DailyRMACount,
        r.Reason,
        COUNT(*) as ReasonCount,
        AVG(COALESCE(r.RefundAmount, 0)) as AvgRefundAmount
    FROM RMA r
    WHERE YEAR(r.RMADate) = p_Year 
    AND MONTH(r.RMADate) = p_Month
    GROUP BY DATE(r.RMADate), r.Reason
    ORDER BY RMADay DESC, ReasonCount DESC;
END$$

-- 8. FUNCTION: Check user permissions for RMA operations
CREATE FUNCTION CheckRMAPermission(
    p_UserRole VARCHAR(20),
    p_Operation VARCHAR(20)
) RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_HasPermission BOOLEAN DEFAULT FALSE;
    
    CASE p_UserRole
        WHEN 'Admin' THEN SET v_HasPermission = TRUE;
        WHEN 'Manager' THEN 
            IF p_Operation IN ('CREATE', 'UPDATE', 'READ') THEN
                SET v_HasPermission = TRUE;
            END IF;
        WHEN 'Customer_Service' THEN
            IF p_Operation IN ('CREATE', 'READ', 'UPDATE_STATUS') THEN
                SET v_HasPermission = TRUE;
            END IF;
        WHEN 'Warehouse' THEN
            IF p_Operation IN ('READ', 'UPDATE_STATUS') THEN
                SET v_HasPermission = TRUE;
            END IF;
        WHEN 'Readonly' THEN
            IF p_Operation = 'READ' THEN
                SET v_HasPermission = TRUE;
            END IF;
    END CASE;
    
    RETURN v_HasPermission;
END$$

DELIMITER ;

-- Example usage of stored procedures:
/*
-- Create a new RMA
CALL CreateRMA(1, 1, 1, 'Defective', 'Product not working properly', 'Refund', 'cs_rep1', @rma_id, @result);
SELECT @rma_id, @result;

-- Update RMA status
CALL UpdateRMAStatus(@rma_id, 'Approved', 'manager1', 'Standard defective product claim', NULL, NULL, @update_result);
SELECT @update_result;

-- Get RMA details
CALL GetRMADetails(@rma_id);

-- Get return rates by SKU
CALL GetReturnRatesBySKU();

-- Get return statistics by state
CALL GetReturnStatsByState();

-- Check permissions
SELECT CheckRMAPermission('Customer_Service', 'CREATE') as CanCreate;
*/