Bank API Documentation

Description
The API allows you to create account skins, open balances in three currencies (UAH, USD, EUR), open deposits, withdraw funds, make transfers, and view transaction history. Authentication is performed via JWT tokens.
The API can be tested using PowerShell.


Basic information:
  Base URL: http://127.0.0.1:5000
  Data Format: JSON
  Currencies: "UAH", "USD", "EUR"
  Limits: 5 requests per minute per endpoint



JWT Authentication
After creating an account or logging in, the user receives a JWT token.
The token is passed in the header for secure routes:
-Headers @{ Authorization = "Bearer $token" }


Quick start 
First you need to clone the repository :-> git clone https://github.com/Xandane/Task-For-Piche-LTD
or :-> Code Download ZIP (If you choose a zip, you will need to additionally unpack it into the desired directory.) 

After that, you need to install all the libraries necessary for the API to work.
press WIN R :-> cmd pip install requirements.txt     (this file has all the necessary libraries to work)


Оpen the code in a convenient editor and start testing the API
To get started, let's save the app.py file 
if all libraries are installed and there are no problems, 
the following should appear in the interpreter console:
    "C:\Program Files\Python311\python.exe" "C:\Users\urami\Desktop\Piche LTD tst\app.py" 
     * Serving Flask app 'app'
     * Debug mode: on
    WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
     * Running on http://127.0.0.1:5000
    Press CTRL+C to quit
     * Restarting with watchdog (windowsapi)
     * Debugger is active!
     * Debugger PIN: 784-115-925

Next, we move on to powershell for testing the API service.
Step one: Go to the powershell directory where the code is stored.
cd "directory location code"

Step two: create the first user with initial capital in hryvnias
$createBody = @{
    name = "user1"
    password = "password123"
    initial_balance = 1000
} | ConvertTo-Json

$createResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/create_account" -Method Post -Body $createBody -ContentType "application/json"
$createResponse | Format-List
$accountId = $createResponse.account_id
$token = $createResponse.token

If created correctly, the surface will be :->  
        account_id : 1
        balances   : @{EUR=; UAH=; USD=}
        token      : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2NvdW50X2lkIjoxLCJleHAiOjE3NjQzMDU4MzJ9.kLHGytyd1Pg_TU6f3blEdWeM
                     AK3uvGuynuBD_z5NnJM

In the interpreter (for example, I use Рycharm)
127.0.0.1 - - [28/Nov/2025 05:57:12] "POST /create_account HTTP/1.1" 200 -
all subsequent valid requests have this response


Step three: add a deposit to the user's account in the selected currency: "UAH", "USD", "EUR"
$depositBody = @{
    account_id = $accountId
    amount = 500 
    currency = "UAH",  or \ "USD", "EUR"
} | ConvertTo-Json

$depositResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/deposit" `
    -Method Post -Body $depositBody -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $token" }

$depositResponse | Format-List

If created correctly, the surface will be :->  
                EUR : @{amount=0.0; code=EUR}
                UAH : @{amount=1500.0; code=UAH}
                USD : @{amount=0.0; code=USD}



Step four: withdraw the user's desired balance to the selected currency
$withdrawBody = @{
    account_id = $accountId
    amount = 200
    currency = "UAH",  or \ "USD", "EUR"
} | ConvertTo-Json

$withdrawResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/withdraw" `
    -Method Post -Body $withdrawBody -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $token" }

$withdrawResponse | Format-List




Step five: to enable transfer, you need to create user number 2
$createBody2 = @{
    name = "user2"
    password = "password456"
    initial_balance = 500
} | ConvertTo-Json

$createResponse2 = Invoke-RestMethod -Uri "http://127.0.0.1:5000/create_account" -Method Post -Body $createBody2 -ContentType "application/json"
$accountId2 = $createResponse2.account_id
$token2 = $createResponse2.token





Step six: perform the transfer
$transferBody = @{
    from_account_id = 1
    to_account_id   = 2
    amount          = 300
    currency        = "UAH",  or \ "USD", "EUR"
} | ConvertTo-Json

$transferResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/transfer" `
    -Method Post `
    -Body $transferBody `
    -ContentType "application/json" `
    -Headers @{ Authorization = "Bearer $token" } | ConvertTo-Json -Depth 5
$transferResponse

expected:
{
    "from":  {
                 "account_id":  1,
                 "balances":  {
                                  "EUR":  {
                                              "amount":  0.0,
                                              "code":  "EUR"
                                          },
                                  "UAH":  {
                                              "amount":  1000.0,
                                              "code":  "UAH"
                                          },
                                  "USD":  {
                                              "amount":  0.0,
                                              "code":  "USD"
                                          }
                              }
             },
    "to":  {
               "account_id":  2,
               "balances":  {
                                "EUR":  {
                                            "amount":  0.0,
                                            "code":  "EUR"
                                        },
                                "UAH":  {
                                            "amount":  800.0,
                                            "code":  "UAH"
                                        },
                                "USD":  {
                                            "amount":  0.0,
                                            "code":  "USD"
                                        }
                            }
           }
}


Get the user's balance It is important to specify the user ID. 
$balanceResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/balance" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $token or $token2 or $token3 ....depending on their number" }

$balanceResponse | Format-List


transaction history:
$transactionsResponse = Invoke-RestMethod -Uri "http://127.0.0.1:5000/transactions" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $token" }

$transactionsResponse | Format-Table

expected:
action   amount currency recipient timestamp                  user
------   ------ -------- --------- ---------                  ----
deposit   500.0 UAH                2025-11-28T03:59:47.403465    1
withdraw  200.0 UAH                2025-11-28T04:03:28.158803    1
transfer  300.0 UAH      2         2025-11-28T04:06:19.288057    1



API errors
Code Reason
400 Invalid amount, Unsupported currency, Username invalid or exists
403 Unauthorized (invalid account_id)
404 Recipient not found
500 Internal server error (server failure)



