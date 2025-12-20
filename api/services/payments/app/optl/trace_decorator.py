from functools import wraps
import inspect
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def trace_repository_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # FIXED: Handle string and class model attribute
            model = getattr(self, 'model', 'UnknownModel')
            if isinstance(model, str):
                model_name = model
            else:
                model_name = getattr(model, '__name__', str(model))
            
            span_name = f"{model_name}.{operation_name}"
            
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("repository.model", model_name)
                span.set_attribute("repository.operation", operation_name)
                
                if operation_name == "get_by_id" and args:
                    span.set_attribute("repository.id", str(args[0]))
                elif operation_name == "get_all" and len(args) >= 2:
                    span.set_attribute("repository.skip", args[0])
                    span.set_attribute("repository.limit", args[1])
                elif operation_name == "update" and args:
                    span.set_attribute("repository.id", str(args[0]))
                elif operation_name == "delete" and args:
                    span.set_attribute("repository.id", str(args[0]))
                elif operation_name == "exists" and args:
                    span.set_attribute("repository.id", str(args[0]))
                
                # Add specific attributes for payment repository methods
                if operation_name in ["get_payment_by_id", "update_payment_status", 
                                     "update_payment_stripe_id", "update_payment_metadata",
                                     "update_payment_client_secret"] and args:
                    span.set_attribute("payment.id", str(args[0]))
                elif operation_name == "get_payment_by_order_id" and args:
                    span.set_attribute("order.id", str(args[0]))
                elif operation_name == "get_payment_by_stripe_id" and args:
                    span.set_attribute("stripe.id", str(args[0]))
                elif operation_name == "list_payments_by_user" and len(args) >= 1:
                    span.set_attribute("user.id", str(args[0]))
                    if len(args) >= 3:
                        span.set_attribute("repository.skip", args[1])
                        span.set_attribute("repository.limit", args[2])
                
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator

def trace_service_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            service_name = self.__class__.__name__
            span_name = f"{service_name}.{operation_name}"
            
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("service.name", service_name)
                span.set_attribute("service.operation", operation_name)
                
                sig = inspect.signature(func)
                params = sig.parameters
                args_list = list(args)
                
                for i, (param_name, param) in enumerate(list(params.items())[1:], 0):
                    if i < len(args_list):
                        value = args_list[i]
                    elif param_name in kwargs:
                        value = kwargs[param_name]
                    else:
                        continue
                    
                    if param_name == "request" and hasattr(value, 'url'):
                        span.set_attribute("http.url", str(value.url))
                        span.set_attribute("http.method", value.method)
                    elif param_name == "user_id":
                        span.set_attribute("user.id", str(value))
                    elif param_name == "order_id":
                        span.set_attribute("order.id", str(value))
                    elif param_name == "payment_id":
                        span.set_attribute("payment.id", str(value))
                    elif param_name.endswith("_data"):
                        data_str = str(value)[:100]
                        span.set_attribute(f"data.{param_name}", data_str)
                
                try:
                    result = await func(self, *args, **kwargs)
                    span.set_attribute("service.success", True)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_attribute("service.error", True)
                    span.set_attribute("service.error_type", type(e).__name__)
                    raise
                
        return wrapper
    return decorator