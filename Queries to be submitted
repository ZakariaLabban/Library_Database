-- Complex Queries
--Q1:Identify Top 5 Borrowed Books in the Last Year

SELECT br.Title, COUNT(b.BookID) AS Borrow_Count
FROM Borrows b
JOIN Books_for_Rent br ON b.BookID = br.BookID
WHERE b.Date_Out >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY br.Title
ORDER BY Borrow_Count DESC
LIMIT 5;

--Q2: List Customers Who Have Unreturned Books Past Due Date

SELECT c.Username, c.First_Name, c.Last_Name, b.BookID, br.Title, b.Due_Date, b.Penalty,
       (b.Penalty + (CURRENT_DATE - b.Due_Date) * 0.5) AS Fine_Amount
FROM Borrows b
JOIN Customer c ON b.Username = c.Username
JOIN Books_for_Rent br ON b.BookID = br.BookID
WHERE b.Status = 'Borrowed'
AND b.Due_Date < CURRENT_DATE;



--Q4: Branch with the Highest Number of Rentals

SELECT b.BranchID, COUNT(br.BookID) AS Rentals_Count
FROM Borrows br
JOIN Books_for_Rent b ON br.BookID = b.BookID
GROUP BY b.BranchID
ORDER BY Rentals_Count DESC
LIMIT 1;

--Q5: Retrieve the total amount each customer has spent on book purchases and item purchases and the most frequently visited branch.

SELECT 
    c.Username,
    c.First_Name,
    c.Last_Name,
    COALESCE(SUM(b.Quantity * bs.Price), 0) AS Total_Book_Spending,
    COALESCE(SUM(i.Quantity * it.Price), 0) AS Total_Item_Spending,
    (SELECT BranchID 
     FROM Buys_Books b2 
     WHERE b2.Username = c.Username 
     GROUP BY BranchID 
     ORDER BY COUNT(*) DESC 
     LIMIT 1) AS Favorite_Branch
FROM 
    Customer c
LEFT JOIN Buys_Books b ON c.Username = b.Username
LEFT JOIN Books_for_Sale bs ON b.ISBN = bs.ISBN
LEFT JOIN Purchases_Items i ON c.Username = i.Username
LEFT JOIN Items it ON i.Barcode = it.Barcode
GROUP BY 
    c.Username, c.First_Name, c.Last_Name;

--Q6: Categorize customers into segments (High, Medium, Low spenders) based on their total spending

WITH Customer_Spend AS ( 
    SELECT 
        c.Username, 
        COALESCE(SUM(b.Quantity * bs.Price), 0) + COALESCE(SUM(i.Quantity * it.Price), 0) AS Total_Spending
    FROM 
        Customer c
    LEFT JOIN Buys_Books b ON c.Username = b.Username
    LEFT JOIN Books_for_Sale bs ON b.ISBN = bs.ISBN
    LEFT JOIN Purchases_Items i ON c.Username = i.Username
    LEFT JOIN Items it ON i.Barcode = it.Barcode
    GROUP BY c.Username
)
SELECT 
    Username, 
    CASE 
        WHEN Total_Spending > 500 THEN 'High Spender'
        WHEN Total_Spending BETWEEN 200 AND 500 THEN 'Medium Spender'
        ELSE 'Low Spender'
    END AS Customer_Segment
FROM 
    Customer_Spend;
-- COALESCE Ensures that if either SUM() returns NULL, it defaults to 0 instead, preventing null values from affecting the result.

--Q7: Find the top 5 suppliers who generated the most revenue from their items.

SELECT 
    s.Supp_Name, 
    SUM(i.Price * p.Quantity) AS Total_Revenue
FROM 
    Purchases_Items p
JOIN 
    Items i ON p.Barcode = i.Barcode
JOIN 
    Supplier s ON i.Supp_Name = s.Supp_Name
GROUP BY 
    s.Supp_Name
ORDER BY 
    Total_Revenue DESC
LIMIT 2;

--Q8:List all customers who bought books or items more than once from a single library branch.     
SELECT c.Username, c.First_Name, c.Last_Name, COUNT(b.ISBN) + COUNT(p.Barcode) AS Total_Purchases, b.BranchID
FROM Customer c
LEFT JOIN Buys_Books b ON c.Username = b.Username
LEFT JOIN Purchases_Items p ON c.Username = p.Username
GROUP BY c.Username, c.First_Name, c.Last_Name, b.BranchID
HAVING COUNT(b.ISBN) + COUNT(p.Barcode) > 1;


--Q9:Retrieve staff who manage libraries with the highest number of items

SELECT s.First_Name, s.Last_Name, s.BranchID, SUM(si.Qty_Stored) AS Total_Items
FROM Staff s
JOIN Stores_Items si ON s.BranchID = si.BranchID
WHERE s.Post = 'Manager'
GROUP BY s.First_Name, s.Last_Name, s.BranchID
ORDER BY Total_Items DESC
LIMIT 1;



--Q10: Find library branches that are running low on inventory.

SELECT si.BranchID, l.Address, SUM(si.Qty_Stored) AS Total_Items, SUM(sb.Number_of_Copies) AS Total_Books
FROM Stores_Items si
JOIN Libraryy l ON si.BranchID = l.BranchID
JOIN Stores_booksforsale sb ON si.BranchID = sb.BranchID
GROUP BY si.BranchID, l.Address
HAVING SUM(si.Qty_Stored) + SUM(sb.Number_of_Copies) < 40;


--Q11:Total Revenue from Book and Item Sales by Library Branch

SELECT 
    l.BranchID,
    COALESCE(SUM(bb.Quantity * bfs.Price), 0) AS Book_Sales_Revenue,
    COALESCE(SUM(pi.Quantity * i.Price), 0) AS Item_Sales_Revenue,
    COALESCE(SUM(bb.Quantity * bfs.Price), 0) + COALESCE(SUM(pi.Quantity * i.Price), 0) AS Total_Revenue
FROM 
    Libraryy l
LEFT JOIN Buys_Books bb ON l.BranchID = bb.BranchID
LEFT JOIN Books_for_Sale bfs ON bb.ISBN = bfs.ISBN
LEFT JOIN Purchases_Items pi ON l.BranchID = pi.BranchID
LEFT JOIN Items i ON pi.Barcode = i.Barcode
GROUP BY l.BranchID
ORDER BY Total_Revenue DESC;

--Q12: Customers Who Borrowed and Bought the Same Book Title

SELECT DISTINCT 
    bo.Username, 
    bfr.Title, 
    bb.Date_Time AS Purchase_Date, 
    bo.Date_Out AS Borrow_Date
FROM 
    Borrows bo
JOIN Books_for_Rent bfr ON bo.BookID = bfr.BookID
JOIN Buys_Books bb ON bo.Username = bb.Username AND bfr.ISBN = bb.ISBN;

--Q13: Retrieve librarians working the most hours across all branches.

SELECT s.First_Name, s.Last_Name, s.BranchID, s.Hours
FROM Staff s
WHERE s.Post = 'Librarian'
ORDER BY s.Hours DESC
LIMIT 5;

--VIEWS , TRIGGERS, PROCEDURES, FUNCTIONS

--View 1: This view provides a summary of items supplied by each supplier along with the total quantity supplied
CREATE VIEW Supplier_Supply_Summary AS
SELECT 
    s.Supp_Name, 
    i.Items_Name, 
    SUM(i.Qty_Supplied) AS Total_Supplied
FROM 
    Items i
JOIN 
    Supplier s ON i.Supp_Name = s.Supp_Name
GROUP BY 
    s.Supp_Name, i.Items_Name
ORDER BY 
    s.Supp_Name;

--View2: Customers With Outstanding Penalties

CREATE VIEW Customers_With_Penalties AS
SELECT 
    c.Username, 
    c.First_Name, 
    c.Last_Name, 
    SUM(br.Penalty) AS Total_Penalty
FROM 
    Borrows br
JOIN 
    Customer c ON br.Username = c.Username
WHERE 
    br.Penalty > 0
GROUP BY 
    c.Username, c.First_Name, c.Last_Name
ORDER BY 
    Total_Penalty DESC;



--Trigger1: Automatically Update the Quantity of Books for Sale After a Purchase

CREATE OR REPLACE FUNCTION update_book_stock()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if the number of copies in stock will become negative
    IF (SELECT Number_of_Copies FROM Stores_Booksforsale 
        WHERE BranchID = NEW.BranchID AND ISBN = NEW.ISBN) < NEW.Quantity THEN
        RAISE EXCEPTION 'Not enough copies in stock for ISBN % in branch %', NEW.ISBN, NEW.BranchID;
    END IF;
    
    -- Update the stock after a successful purchase
    UPDATE Stores_Booksforsale
    SET Number_of_Copies = Number_of_Copies - NEW.Quantity
    WHERE BranchID = NEW.BranchID AND ISBN = NEW.ISBN;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_book_stock
AFTER INSERT ON Buys_Books
FOR EACH ROW
EXECUTE FUNCTION update_book_stock();

--Trigger2: Prevent a user from borrowing a new book if they have outstanding penalties in the Borrows table.

CREATE OR REPLACE FUNCTION prevent_borrow_with_overdue()
RETURNS TRIGGER AS $$
BEGIN
    -- Check for overdue books
    IF EXISTS (
        SELECT 1
        FROM Borrows
        WHERE Username = NEW.Username 
        AND Due_Date < CURRENT_DATE      -- Check if due date has passed
        AND Status = 'Borrowed'
    ) THEN
        RAISE EXCEPTION 'User % has overdue books and cannot borrow a new book', NEW.Username;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger to call the function before a new row is inserted
CREATE TRIGGER trigger_prevent_borrow_with_overdue
BEFORE INSERT ON Borrows
FOR EACH ROW
EXECUTE FUNCTION prevent_borrow_with_overdue();


--Function:
CREATE OR REPLACE FUNCTION handle_sale_to_rent()
RETURNS TRIGGER AS $$
DECLARE
    shelf_no INT;
    row_no INT;
    branch_id VARCHAR(10);
    existing_price NUMERIC;  -- To store the price of the existing book, if found
BEGIN
    -- Step 1: Extract Shelf_No and Row_No from BookID
    shelf_no := CAST(SUBSTRING(NEW.BookID FROM POSITION('#' IN NEW.BookID) + 1 FOR 2) AS INT);
    row_no := CAST(SUBSTRING(NEW.BookID FROM POSITION('#' IN NEW.BookID) + 3 FOR 1) AS INT);

    -- Step 2: Get the BranchID from Stores_Booksforsale table
    SELECT BranchID INTO branch_id
    FROM Stores_Booksforsale
    WHERE ISBN = NEW.ISBN
    LIMIT 1;

    -- Check if a valid branch was found
    IF branch_id IS NULL THEN
        RAISE EXCEPTION 'Cannot move book % to rent. It is not stored in any branch.', NEW.ISBN;
    END IF;

    -- Step 3: Check if the book exists in the Books_for_Sale table and has at least one copy
    IF NOT EXISTS (
        SELECT 1
        FROM Stores_Booksforsale
        WHERE ISBN = NEW.ISBN AND BranchID = branch_id AND Number_of_Copies > 0
    ) THEN
        RAISE EXCEPTION 'Cannot move book % to rent, not enough copies available in branch %.', NEW.ISBN, branch_id;
    END IF;

    -- Step 4: Decrease the number of copies for sale by 1
    UPDATE Stores_Booksforsale
    SET Number_of_Copies = Number_of_Copies - 1
    WHERE ISBN = NEW.ISBN AND BranchID = branch_id;

    -- Step 5: Check if there is an existing book with the same ISBN but a different BookID in Books_for_Rent
    SELECT Price INTO existing_price
    FROM Books_for_Rent
    WHERE ISBN = NEW.ISBN
    LIMIT 1;

    -- Step 6: Determine the price of the moved book
    IF existing_price IS NOT NULL THEN
        -- Use the price of the existing book
        RAISE NOTICE 'An existing book with ISBN % is found. Using the same price: %.', NEW.ISBN, existing_price;
    ELSE
        -- Calculate the discounted price
        existing_price := ROUND((SELECT Price FROM Books_for_Sale WHERE ISBN = NEW.ISBN) * (1 - NEW.Discount / 100.0), 2);
        RAISE NOTICE 'No existing book with ISBN % is found. Using the discounted price: %.', NEW.ISBN, existing_price;
    END IF;

    -- Step 7: Insert the book into the Books_for_Rent table
    INSERT INTO Books_for_Rent (
        BookID, ISBN, Title, Genre, Price, Translator, Edition, Pages, Lang, Publisher_Name, Shelf_No, Row_No, BranchID
    )
    SELECT
        NEW.BookID, 
        b.ISBN, 
        b.Title, 
        b.Genre, 
        existing_price,  -- Set the price
        b.Translator, 
        b.Edition, 
        b.Pages, 
        b.Lang, 
        b.Publisher_Name, 
        shelf_no,  -- Extracted Shelf_No
        row_no,    -- Extracted Row_No
        branch_id  -- Derived BranchID
    FROM Books_for_Sale b
    WHERE b.ISBN = NEW.ISBN;

    -- Log the action (optional, for audit purposes)
    RAISE NOTICE 'Book % has been successfully moved from sale to rent in branch % with Shelf_No: %, Row_No: %, and price: %.', NEW.ISBN, branch_id, shelf_no, row_no, existing_price;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for the Sale_to_Rent table
CREATE or REPLACE TRIGGER trigger_handle_sale_to_rent
BEFORE INSERT ON Sale_to_Rent
FOR EACH ROW
EXECUTE FUNCTION handle_sale_to_rent();



--Function: This function checks whether a specific book (based on its Name) is available in a given branch and returns the number of copies available.

CREATE OR REPLACE FUNCTION check_book_availability(Title_input TEXT, branch_id_input VARCHAR)
RETURNS TEXT AS $$
DECLARE
    book_title TEXT;
BEGIN
    SELECT bs.Title
    INTO book_title
    FROM Books_for_Sale bs
    JOIN Stores_Booksforsale sb ON bs.ISBN = sb.ISBN
    WHERE bs.Title = Title_input AND sb.BranchID = branch_id_input;

    RETURN book_title; -- Returns the title if the book is available
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN 'Book not available';
END;
$$ LANGUAGE plpgsql;




--Function: Calculate Total Inventory Value for a Branch
CREATE OR REPLACE FUNCTION total_inventory_value(branch_id VARCHAR)
RETURNS NUMERIC AS $$
DECLARE
    total_value NUMERIC := 0;
BEGIN
    SELECT 
        COALESCE(SUM(bfs.Price * sb.Number_of_Copies), 0) +
        COALESCE(SUM(i.Price * si.Qty_Stored), 0)
    INTO total_value
    FROM 
        Libraryy l
    LEFT JOIN Stores_Booksforsale sb ON l.BranchID = sb.BranchID
    LEFT JOIN Books_for_Sale bfs ON sb.ISBN = bfs.ISBN
    LEFT JOIN Stores_Items si ON l.BranchID = si.BranchID
    LEFT JOIN Items i ON si.Barcode = i.Barcode
    WHERE l.BranchID = branch_id;

    RETURN total_value;
END;
$$ LANGUAGE plpgsql;






--Stored Procedure1: Transfer Book Stock Between Branches
CREATE OR REPLACE PROCEDURE transfer_book_stock(
    from_branch VARCHAR,
    to_branch VARCHAR,
    book_isbn CHAR(13), -- Renamed parameter to avoid conflict
    transfer_quantity INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check if the from_branch has enough stock
    IF NOT EXISTS (
        SELECT 1 
        FROM Stores_Booksforsale 
        WHERE BranchID = from_branch AND ISBN = book_isbn AND Number_of_Copies >= transfer_quantity
    ) THEN
        RAISE EXCEPTION 'Insufficient stock in branch % for book %', from_branch, book_isbn;
    END IF;

    -- Deduct stock from from_branch
    UPDATE Stores_Booksforsale
    SET Number_of_Copies = Number_of_Copies - transfer_quantity
    WHERE BranchID = from_branch AND ISBN = book_isbn;

    -- Add stock to to_branch
    INSERT INTO Stores_Booksforsale (BranchID, ISBN, Number_of_Copies)
    VALUES (to_branch, book_isbn, transfer_quantity)
    ON CONFLICT (BranchID, ISBN) 
    DO UPDATE SET Number_of_Copies = Stores_Booksforsale.Number_of_Copies + transfer_quantity;
END;
$$;





-----BONUSES

--Recursive Query: Track Borrowing Chains for a Book

WITH RECURSIVE Borrowing_Chain AS (
    -- Base Case: Get all borrowers of the book
    SELECT 
        b.Username, 
        c.First_Name, 
        c.Last_Name, 
        b.BookID, 
        b.Date_Out, 
        b.Due_Date, 
        b.Penalty,
        1 AS Chain_Level
    FROM Borrows b
    JOIN Customer c ON b.Username = c.Username
    WHERE b.BookID = '0000000002431#001'

    UNION ALL

    -- Recursive Case: Find the next borrower after the previous one returned the book
    SELECT 
        next_borrower.Username, 
        c.First_Name, 
        c.Last_Name, 
        next_borrower.BookID, 
        next_borrower.Date_Out, 
        next_borrower.Due_Date, 
        next_borrower.Penalty,
        bc.Chain_Level + 1
    FROM Borrows next_borrower
    JOIN Borrowing_Chain bc 
        ON next_borrower.BookID = bc.BookID 
        AND next_borrower.Date_Out > bc.Due_Date
    JOIN Customer c ON next_borrower.Username = c.Username
)
SELECT 
    Username, 
    First_Name, 
    Last_Name, 
    BookID, 
    Date_Out, 
    Due_Date, 
    Penalty, 
    Chain_Level
FROM Borrowing_Chain
ORDER BY Chain_Level, Date_Out;






--SECURITY MECHANISM 1: User Roles and Permissions
-- Creating roles
CREATE ROLE Librariann;
CREATE ROLE Managerr;
CREATE ROLE Customerr;

-- Granting permissions to Librarian
GRANT SELECT, INSERT, UPDATE ON Borrows TO Librariann;
GRANT SELECT ON Customer, Stores_Items, Stores_Booksforsale TO Librariann;

-- Granting full access to Admin
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO Managerr;

-- Granting read-only access to Customers
GRANT SELECT ON Books_for_Sale, Books_for_Rent TO Customerr;




--SECURITY MECHANISM 2: Restrict data access based on the user’s role or identity
-- Enable row-level security on the Borrows table
ALTER TABLE Borrows ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow only the borrower to see their records
CREATE POLICY Borrower_Policy
ON Borrows
USING (Username = CURRENT_USER);

-- Apply the policy
ALTER TABLE Borrows FORCE ROW LEVEL SECURITY;


--SECURITY MECHANISM 3: SQL INJECTION

--SQL INJECTION IS WHEN TRYING TO INSERT:
SELECT * FROM Customer WHERE Username = 'en01' OR '1'='1';

--QUERY:
PREPARE find_customer (VARCHAR) AS
SELECT * FROM Customer WHERE Username = $1;
EXECUTE find_customer('en01');


--Security Mechanism 4: Encryption and Decryption

CREATE EXTENSION pgcrypto;
ALTER TABLE Authentication_System DROP CONSTRAINT chk_passcode;
ALTER TABLE Authentication_System
ALTER COLUMN Passcode TYPE BYTEA USING pgp_sym_encrypt(Passcode::TEXT, 's3cUr3!kEy#2023@P0stgreSQL^');


--Encryption:
Insert into Authentication_System Values('myh17@gmail.com',pgp_sym_encrypt('Qwerty123#@', 's3cUr3!kEy#2023@P0stgreSQL^'));

--Decryption:
SELECT Email,
       pgp_sym_decrypt(Passcode, 's3cUr3!kEy#2023@P0stgreSQL^') AS Decrypted_Passcode
FROM Authentication_System
WHERE Email = 'myh17@gmail.com';
