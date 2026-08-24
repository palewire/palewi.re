---
title: 'SQL Recipe: Federal gov''t working days between two dates'
slug: sql-recipe-the-number-of-federal-government-working-days-between-two-dates
published_at: '2007-02-14T07:52:24-08:00'
wordpress_id: 49
---
<p>If you'd ever like to programmatically determine the number of federal working days between two dates, here's a quick and dirty solution I cooked up the other day in Microsoft SQL Server. It can be useful in monitering deadlines and evaluating bureaucratic processing speeds (say, for example, a log of Freedom of Information Act requests).</p>



<p>It's a three-step process.</p>



<ol>

	<li>Create a calendar table that distinguishes working days from weekends and holidays.</li>

	<li>Create a user-defined function that will use that calendar to count the number of working days between two dates.</li>

	<li>Count the days.</li>

</ol>



<p>Below you can find a calendar creation script I adapted from one published on <a href="http://classicasp.aspfaq.com/date-time-routines-manipulation/how-do-i-count-the-number-of-business-days-between-two-dates.html" target="_blank">aspfaq.com</a>. Besides distinguishing weekdays from weekends, it marks off all federal holidays -- as specificed by the U.S. Office of Personnel Management -- from Jan. 1, 2000 to Dec. 31, 2010.</p>



<p>First we create the calendar table. It will have three fields, one for the date and then two binary fields, one that will automatically determine the weekdays using the DATEPART function, and another that we will use later to designate working days.</p>



<pre lang="SQL">CREATE TABLE dbo.FederalCalendar (

dt SMALLDATETIME PRIMARY KEY CLUSTERED,

isWeekDay AS CONVERT(BIT, CASE

WHEN DATEPART(dw, dt) IN (1,7) THEN 0

ELSE 1 END),

isWorkDay BIT DEFAULT 1

);

GO</pre>



<p>Next we need to populate the date field, dt, with the range of days in our calendar. In this case, it will be from Jan. 1, 2000 through Dec. 31, 2010.</p>



<pre lang="SQL">DECLARE @dt SMALLDATETIME;

SET @dt = '20000101';

WHILE @dt <= '20101231'

BEGIN

INSERT dbo.FederalCalendar(dt) SELECT @dt;

SET @dt = @dt + 1;

END</pre>



<p>Then winnow down our working days field by eliminating the weekends.</p>



<pre lang="SQL">UPDATE dbo.FederalCalendar

SET isWorkDay = 0

WHERE isWeekday = 0;</pre>



<p>And finish the job by knocking out all of the federal holidays. Of course you could modify this to reflect any other schedule you'd like to work with, such as trading days on Wall Street or the official holidays in your state.</p>



<pre lang="SQL">UPDATE dbo.FederalCalendar

SET isWorkDay = 0

WHERE isWorkDay = 1

AND dt IN

(

--2000 Federal Holidays

-- New Year's Day holiday was observed on 12/31/1999

'20000117', -- Martin Luther King's Birthday

'20000221', -- George Washington's Birthday

'20000529', -- Memorial Day

'20000704', -- Independence Day

'20000904', -- Labor Day

'20001009', -- Columbus Day

'20001110', -- Veterans Day

'20001123', -- Thanksgiving Day

'20001225', -- Christmas Day



--2001 Federal Holidays

'20010101', -- New Year's Day

'20010115', -- Martin Luther King's Birthday

'20010219', -- George Washington's Birthday

'20010528', -- Memorial Day

'20010704', -- Independence Day

'20010903', -- Labor Day

'20011008', -- Columbus Day

'20011112', -- Veterans Day

'20011122', -- Thanksgiving Day

'20011225', -- Christmas Day



--2002 Federal Holidays

'20020101', -- New Year's Day

'20020117', -- Martin Luther King's Birthday

'20020218', -- George Washington's Birthday

'20020527', -- Memorial Day

'20020704', -- Independence Day

'20020902', -- Labor Day

'20021014', -- Columbus Day

'20021111', -- Veterans Day

'20021128', -- Thanksgiving Day

'20021225', -- Christmas Day



--2003 Federal Holidays

'20030101', -- New Year's Day

'20030120', -- Martin Luther King's Birthday

'20030217', -- George Washington's Birthday

'20030526', -- Memorial Day

'20030704', -- Independence Day

'20030901', -- Labor Day

'20031013', -- Columbus Day

'20031111', -- Veterans Day

'20031127', -- Thanksgiving Day

'20031225', -- Christmas Day



--2004 Federal Holidays

'20040101', -- New Year's Day

'20040119', -- Martin Luther King's Birthday

'20040216', -- George Washington's Birthday

'20040531', -- Memorial Day

'20040705', -- Independence Day

'20040906', -- Labor Day

'20041011', -- Columbus Day

'20041111', -- Veterans Day

'20041125', -- Thanksgiving Day

'20041224', -- Christmas Day



--2005 Federal Holidays

'20041231', -- New Year's Day

'20050117', -- Martin Luther King's Birthday

'20050221', -- George Washington's Birthday

'20050530', -- Memorial Day

'20050704', -- Independence Day

'20050905', -- Labor Day

'20051010', -- Columbus Day

'20051111', -- Veterans Day

'20051124', -- Thanksgiving Day

'20051226', -- Christmas Day



--2006 Federal Holidays

'20060102', -- New Year's Day

'20060116', -- Martin Luther King's Birthday

'20060220', -- George Washington's Birthday

'20060529', -- Memorial Day

'20060704', -- Independence Day

'20060904', -- Labor Day

'20061009', -- Columbus Day

'20061110', -- Veterans Day

'20061123', -- Thanksgiving Day

'20061225', -- Christmas Day



--2007 Federal Holidays

'20070101', -- New Years Day

'20070115', -- Martin Luther King's Birthday

'20070219', -- George Washington's Birthday

'20070528', -- Memorial Day

'20070704', -- Independence Day

'20070903', -- Labor Day

'20071008', -- Columbus Day

'20071112', -- Veterans Day

'20071122', -- Thanksgiving Day

'20071225',  -- Christmas Day



--2008 Federal Holidays

'20080101', -- New Years Day

'20080121', -- Martin Luther King's Birthday

'20080218', -- George Washington's Birthday

'20080526', -- Memorial Day

'20080704', -- Independence Day

'20080901', -- Labor Day

'20081013', -- Columbus Day

'20081111', -- Veterans Day

'20081127', -- Thanksgiving Day

'20081225',  -- Christmas Day



--2009 Federal Holidays

'20090101', -- New Years Day

'20090119', -- Martin Luther King's Birthday

'20090216', -- George Washington's Birthday

'20090525', -- Memorial Day

'20090703', -- Independence Day

'20090907', -- Labor Day

'20091012', -- Columbus Day

'20091111', -- Veterans Day

'20091126', -- Thanksgiving Day

'20091225',  -- Christmas Day



--2010 Federal Holidays

'20100101', -- New Years Day

'20100118', -- Martin Luther King's Birthday

'20100215', -- George Washington's Birthday

'20100531', -- Memorial Day

'20100705', -- Independence Day

'20100906', -- Labor Day

'20101011', -- Columbus Day

'20101111', -- Veterans Day

'20101125', -- Thanksgiving Day

'20101225'  -- Christmas Day

);</pre>



<p>Now that the calendar's done, here's a script that will create a user-defined function to take two dates and count the number of federal working days between the them.</p>



<pre lang="SQL">CREATE FUNCTION [dbo].[FederalWorkingDays]

(

@startDate SMALLDATETIME,

@endDate SMALLDATETIME

)

RETURNS INT

AS

BEGIN



DECLARE @result INT



SELECT @result = COUNT(*)

FROM dbo.FederalCalendar

WHERE dt >= @startDate

AND dt <= @endDate

AND isWorkDay = 1;



RETURN  @result



END</pre>



<p>Once you've run that, all you should need to do to is write a query that uses your new function. Here are two examples:</p>



<pre lang="SQL">SELECT dbo.FederalWorkingDays(datefield1, datefield2)

FROM table



SELECT dbo.FederalWorkingDays('01/01/2007', '02/14/2007')</pre>



<p>And that's the end of our journey. I hope it can be helpful to somebody. As always, if there's something screwed up or missed, just drop a comment. We'll sort things out.</p>