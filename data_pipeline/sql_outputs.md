# SQL Query Outputs

Fixed currency baseline: **1 GBP = 105.50 INR**

## 1. SELECT + WHERE
```sql
SELECT title, price_inr, rating
            FROM books
            WHERE rating >= 4
            ORDER BY rating DESC, title
            LIMIT 10;
```

| title                                    |   price_inr |   rating |
|:-----------------------------------------|------------:|---------:|
| 1,000 Places to See Before You Die       |     2751.44 |        5 |
| A Time of Torment (Charlie Parker #14)   |     5100.92 |        5 |
| Atlas Shrugged                           |     2804.19 |        5 |
| Bright Lines                             |     4121.88 |        5 |
| Crazy Rich Asians (Crazy Rich Asians #1) |     5183.22 |        5 |
| Dear Mr. Knightley                       |     1182.66 |        5 |
| Digital Fortress                         |     6119    |        5 |
| Finders Keepers (Bill Hodges Trilogy #2) |     5647.42 |        5 |
| Inferno (Robert Langdon #4)              |     4325.5  |        5 |
| Kitchens of the Great Midwest            |     6034.6  |        5 |

## 2. ORDER BY + LIMIT
```sql
SELECT title, price_inr
            FROM books
            ORDER BY price_inr DESC
            LIMIT 10;
```

| title                                                                  |   price_inr |
|:-----------------------------------------------------------------------|------------:|
| Last One Home (New Beginnings #1)                                      |     6327.89 |
| Boar Island (Anna Pigeon #19)                                          |     6275.14 |
| The Improbability of Love                                              |     6271.98 |
| Miller's Valley                                                        |     6175.97 |
| Digital Fortress                                                       |     6119    |
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1) |     6087.35 |
| Kitchens of the Great Midwest                                          |     6034.6  |
| A Year in Provence (Provence #1)                                       |     6000.84 |
| The Dinner Party                                                       |     5964.97 |
| The Past Never Ends                                                    |     5960.75 |

## 3. DISTINCT
```sql
SELECT DISTINCT category_name
            FROM categories
            ORDER BY category_name;
```

| category_name   |
|:----------------|
| Fiction         |
| Mystery         |
| Travel          |

## 4. BETWEEN
```sql
SELECT title, price_gbp
            FROM books
            WHERE price_gbp BETWEEN 20 AND 40
            ORDER BY price_gbp;
```

| title                                                                                             |   price_gbp |
|:--------------------------------------------------------------------------------------------------|------------:|
| Blood Defense (Samantha Brinkman #1)                                                              |       20.3  |
| Delivering the Truth (Quaker Midwife Mystery #1)                                                  |       20.89 |
| Tuesday Nights in 1980                                                                            |       21.04 |
| Hystopia: A Novel                                                                                 |       21.96 |
| The Art of Fielding                                                                               |       22.1  |
| Big Little Lies                                                                                   |       22.11 |
| The Da Vinci Code (Robert Langdon #2)                                                             |       22.96 |
| The Silkworm (Cormoran Strike #2)                                                                 |       23.05 |
| The Road to Little Dribbling: Adventures of an American in Britain (Notes From a Small Island #2) |       23.21 |
| Three-Martini Lunch                                                                               |       23.21 |
| My Mrs. Brown                                                                                     |       24.48 |
| Career of Evil (Cormoran Strike #3)                                                               |       24.72 |
| The Little Paris Bookshop                                                                         |       24.73 |
| The Mysterious Affair at Styles (Hercule Poirot #1)                                               |       24.8  |
| Cometh the Hour (The Clifton Chronicles #6)                                                       |       25.01 |
| What Happened on Beale Street (Secrets of the South Mysteries #2)                                 |       25.37 |
| Extreme Prey (Lucas Davenport #26)                                                                |       25.4  |
| The First Hostage (J.B. Collins #2)                                                               |       25.85 |
| 1,000 Places to See Before You Die                                                                |       26.08 |
| The Nightingale                                                                                   |       26.26 |
| Still Life with Bread Crumbs                                                                      |       26.41 |
| Atlas Shrugged                                                                                    |       26.58 |
| Poisonous (Max Revere Novels #3)                                                                  |       26.8  |
| Eligible (The Austen Project #4)                                                                  |       27.09 |
| The Widow                                                                                         |       27.26 |
| The Infinities                                                                                    |       27.41 |
| The Time Keeper                                                                                   |       27.88 |
| The Shack                                                                                         |       28.03 |
| Mr. Mercedes (Bill Hodges Trilogy #1)                                                             |       28.9  |
| The Great Railway Bazaar                                                                          |       30.54 |
| The Bette Davis Club                                                                              |       30.66 |
| Siddhartha                                                                                        |       34.22 |
| Most Wanted                                                                                       |       35.28 |
| Vagabonding: An Uncommon Guide to the Art of Long-Term World Travel                               |       36.94 |
| Under the Tuscan Sun                                                                              |       37.33 |
| In the Woods (Dublin Murder Squad #1)                                                             |       38.38 |
| Neither Here nor There: Travels in Europe                                                         |       38.95 |
| Bright Lines                                                                                      |       39.07 |
| A Man Called Ove                                                                                  |       39.72 |

## 5. IN
```sql
SELECT title, category_id, rating
            FROM books
            WHERE category_id IN (1, 2, 3)
            ORDER BY rating DESC, title
            LIMIT 10;
```

| title                                    |   category_id |   rating |
|:-----------------------------------------|--------------:|---------:|
| 1,000 Places to See Before You Die       |             3 |        5 |
| A Time of Torment (Charlie Parker #14)   |             2 |        5 |
| Atlas Shrugged                           |             1 |        5 |
| Bright Lines                             |             1 |        5 |
| Crazy Rich Asians (Crazy Rich Asians #1) |             1 |        5 |
| Dear Mr. Knightley                       |             1 |        5 |
| Digital Fortress                         |             1 |        5 |
| Finders Keepers (Bill Hodges Trilogy #2) |             1 |        5 |
| Inferno (Robert Langdon #4)              |             1 |        5 |
| Kitchens of the Great Midwest            |             1 |        5 |

## 6. JOIN
```sql
SELECT c.category_name, b.title, b.rating, b.price_inr
            FROM books AS b
            JOIN categories AS c ON b.category_id = c.category_id
            ORDER BY b.rating DESC, b.price_inr DESC, b.title
            LIMIT 10;
```

| category_name   | title                                                                    |   rating |   price_inr |
|:----------------|:-------------------------------------------------------------------------|---------:|------------:|
| Fiction         | Digital Fortress                                                         |        5 |     6119    |
| Fiction         | Kitchens of the Great Midwest                                            |        5 |     6034.6  |
| Fiction         | Finders Keepers (Bill Hodges Trilogy #2)                                 |        5 |     5647.42 |
| Fiction         | The Husband's Secret                                                     |        5 |     5539.8  |
| Mystery         | The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |     5517.65 |
| Fiction         | The Regional Office Is Under Attack!                                     |        5 |     5418.48 |
| Fiction         | We Love You, Charlie Freeman                                             |        5 |     5303.48 |
| Fiction         | Crazy Rich Asians (Crazy Rich Asians #1)                                 |        5 |     5183.22 |
| Mystery         | A Time of Torment (Charlie Parker #14)                                   |        5 |     5100.92 |
| Fiction         | Private Paris (Private #10)                                              |        5 |     5022.85 |

## JOIN: SQL vs pandas.merge

### SQL `pd.read_sql` result
| category_name   | title                                                                    |   rating |   price_inr |
|:----------------|:-------------------------------------------------------------------------|---------:|------------:|
| Fiction         | Digital Fortress                                                         |        5 |     6119    |
| Fiction         | Kitchens of the Great Midwest                                            |        5 |     6034.6  |
| Fiction         | Finders Keepers (Bill Hodges Trilogy #2)                                 |        5 |     5647.42 |
| Fiction         | The Husband's Secret                                                     |        5 |     5539.8  |
| Mystery         | The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |     5517.65 |
| Fiction         | The Regional Office Is Under Attack!                                     |        5 |     5418.48 |
| Fiction         | We Love You, Charlie Freeman                                             |        5 |     5303.48 |
| Fiction         | Crazy Rich Asians (Crazy Rich Asians #1)                                 |        5 |     5183.22 |
| Mystery         | A Time of Torment (Charlie Parker #14)                                   |        5 |     5100.92 |
| Fiction         | Private Paris (Private #10)                                              |        5 |     5022.85 |

### pandas `pd.merge` result
| category_name   | title                                                                    |   rating |   price_inr |
|:----------------|:-------------------------------------------------------------------------|---------:|------------:|
| Fiction         | Digital Fortress                                                         |        5 |     6119    |
| Fiction         | Kitchens of the Great Midwest                                            |        5 |     6034.6  |
| Fiction         | Finders Keepers (Bill Hodges Trilogy #2)                                 |        5 |     5647.42 |
| Fiction         | The Husband's Secret                                                     |        5 |     5539.8  |
| Mystery         | The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |     5517.65 |
| Fiction         | The Regional Office Is Under Attack!                                     |        5 |     5418.48 |
| Fiction         | We Love You, Charlie Freeman                                             |        5 |     5303.48 |
| Fiction         | Crazy Rich Asians (Crazy Rich Asians #1)                                 |        5 |     5183.22 |
| Mystery         | A Time of Torment (Charlie Parker #14)                                   |        5 |     5100.92 |
| Fiction         | Private Paris (Private #10)                                              |        5 |     5022.85 |

**Equivalent output:** `True`
