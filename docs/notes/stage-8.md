
after using pgbouncer, we could see more drops in response time but overall, the issue of our high response time seems to be not related to db pooling.

before pgbouncer :

![alt text](image-1.png)

after pgbouncer :

![alt text](image.png)


we learned that only pgbouncer does not solve the issue, lets see what takes our time :

![alt text](image-2.png)

we can see some requests are taking 12 seconds to respond!!!

but to find the issue, we should not check the one that took the longest, as probably all parts of the request took a long time, lets revise a rather normal one.

POST /register :

![alt text](image-3.png)

POST /register :

![alt text](image-4.png)

POST /login :

![alt text](image-5.png)

as we can see AuthService takes sooo long and it is not responding in enough time to be considered ok.

butttt after :


![alt text](image-6.png)


when i  ran the k6 tests, for some reason i got /me 401 unauthorized over and over again.

the issue? in test, one user is using logout and blacklisting the token, the other concurrent user is trying to login using that token.

this is an error that we encountered when running k6, whilst our ordersDB had not been using db pooling :

2025-12-28 16:41:35,563 - routes.order_routes - ERROR - Create order error: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00 (Background on this error at: https://sqlalche.me/e/20/3o7r)⁠




otel.status_code	
ERROR
otel.status_description	
AioRpcError: <AioRpcError of RPC that terminated with:
	status = StatusCode.INTERNAL
	details = "This session is provisioning a new connection; concurrent operations are not permitted (Background on this error at: https://sqlalche.me/e/20/isce)"
	debug_error_string = "UNKNOWN:Error received from peer  {grpc_message:"This session is provisioning a new connection; concurrent operations are not permitted (Background on this error at: https://sqlalche.me/e/20/isce)", grpc_status:13}"
>
service.name	
PaymentGRPCClient

what is this error? Key Issue: ISCE Error
The error code isce stands for "This session is provisioning a new connection; concurrent operations are not permitted". This occurs when:

Multiple async operations are trying to use the same database session simultaneously

The session hasn't fully initialized its database connection yet

SQLAlchemy prevents concurrent operations during this provisioning phase