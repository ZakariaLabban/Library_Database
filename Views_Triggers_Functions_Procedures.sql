--VIEWS:

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
Test Case:
SELECT * FROM Customers_With_Penalties;

--Triggers:

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



--FUNCTIONS:

--Function1: This function checks whether a specific book (based on its Name) is available in a given branch and returns the number of copies available.

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


--Example usage:
SELECT check_book_availability('Electronics', 'LIBTECH01');

--Function2: Calculate Total Inventory Value for a Branch

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

-- Example usage:
-- SELECT total_inventory_value('LIBTECH01');




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


--example: CALL transfer_book_stock('LIBTECH01', 'LIBTECH02', '0000000003421', 5);





