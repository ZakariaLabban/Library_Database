

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



--Q8:   --List all customers who bought books or items more than once from a single library branch.     

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


--Q11: Total Revenue from Book and Item Sales by Library Branch

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

