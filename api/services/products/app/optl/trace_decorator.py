from functools import wraps
from opentelemetry import trace
import inspect
from fastapi import Request, UploadFile

tracer = trace.get_tracer(__name__)
def trace_repository_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get model name from class name
            class_name = self.__class__.__name__
            if class_name.endswith('Repository'):
                model_name = class_name[:-10]  # Remove 'Repository'
            else:
                model_name = class_name
            
            span_name = f"{model_name}.{operation_name}"
            
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("repository.name", model_name)
                span.set_attribute("repository.operation", operation_name)
                span.set_attribute("repository.database", "mongodb")
                
                # Add specific attributes based on operation
                if operation_name == "get_product_by_id" and args:
                    span.set_attribute("product.id", str(args[0]))
                elif operation_name == "get_product_by_name" and args:
                    span.set_attribute("product.name", str(args[0]))
                elif operation_name == "list_products" and len(args) >= 2:
                    span.set_attribute("repository.skip", args[0])
                    span.set_attribute("repository.limit", args[1])
                    if len(args) >= 3 and args[2]:
                        span.set_attribute("product.search_query", str(args[2]))
                    if len(args) >= 4 and args[3]:
                        span.set_attribute("product.tags", str(args[3]))
                elif operation_name == "update_product" and args:
                    span.set_attribute("product.id", str(args[0]))
                    span.set_attribute("update.fields", str(list(kwargs.get('update_data', {}).keys()))[:100])
                elif operation_name == "delete_product" and args:
                    span.set_attribute("product.id", str(args[0]))
                elif operation_name == "update_product_images" and args:
                    span.set_attribute("product.id", str(args[0]))
                    if len(args) >= 2:
                        span.set_attribute("image.count", len(args[1]))
                elif operation_name == "update_inventory" and args:
                    span.set_attribute("product.id", str(args[0]))
                    if len(args) >= 2:
                        span.set_attribute("inventory.new_stock", args[1])
                elif operation_name == "get_products_by_tags" and args:
                    span.set_attribute("tags.count", len(args[0]))
                    if len(args) >= 2:
                        span.set_attribute("repository.skip", args[1])
                    if len(args) >= 3:
                        span.set_attribute("repository.limit", args[2])
                elif operation_name == "count_products" and args:
                    if len(args) >= 1 and args[0]:
                        span.set_attribute("product.search_query", str(args[0]))
                    if len(args) >= 2 and args[1]:
                        span.set_attribute("product.tags", str(args[1]))
                
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator

def trace_client_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            span_name = f"ProductImageClient.{operation_name}"
            
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("client.name", "ProductImageClient")
                span.set_attribute("client.operation", operation_name)
                span.set_attribute("client.base_url", self.base_url)
                
                if operation_name == "upload_image":
                    if args and isinstance(args[0], UploadFile):
                        span.set_attribute("file.filename", args[0].filename)
                        span.set_attribute("file.content_type", args[0].content_type)
                    if len(args) >= 2:
                        span.set_attribute("subdirectory", str(args[1]))
                    if kwargs.get('metadata'):
                        span.set_attribute("metadata.present", "true")
                        
                elif operation_name == "upload_images":
                    if args and isinstance(args[0], list):
                        span.set_attribute("files.count", len(args[0]))
                    if len(args) >= 2:
                        span.set_attribute("subdirectory", str(args[1]))
                    if kwargs.get('metadata_list'):
                        span.set_attribute("metadata_list.count", str(len(kwargs['metadata_list'])))
                        
                elif operation_name == "delete_image" and args:
                    span.set_attribute("file.id", str(args[0]))
                    
                elif operation_name == "delete_images" and args:
                    span.set_attribute("files.count", len(args[0]))
                    
                elif operation_name == "validate_image" and args:
                    span.set_attribute("image.url", str(args[0]))
                    
                elif operation_name == "extract_file_id" and args:
                    span.set_attribute("image.url", str(args[0]))
                    
                elif operation_name == "cleanup_unused_images":
                    if args:
                        span.set_attribute("used_images.count", len(args[0]))
                    if len(args) >= 2:
                        span.set_attribute("subdirectory", str(args[1]))
                        
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def trace_service_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            span_name = f"ProductService.{operation_name}"
            
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("service.name", "ProductService")
                span.set_attribute("service.operation", operation_name)
                
                if operation_name == "create_product":
                    if len(args) >= 2:
                        span.set_attribute("product.name", args[1].name)
                        span.set_attribute("product.price", str(args[1].price))
                        span.set_attribute("product.stock", str(args[1].stock))
                        span.set_attribute("product.tags_count", str(len(args[1].tags)))
                        span.set_attribute("product.images_count", str(len(args[1].images)))
                        
                elif operation_name == "create_product_with_images":
                    if len(args) >= 2:
                        span.set_attribute("product.name", args[1].name)
                        span.set_attribute("product.price", str(args[1].price))
                    if len(args) >= 3:
                        span.set_attribute("image_files.count", len(args[2]))
                        
                elif operation_name == "get_product" and len(args) >= 2:
                    span.set_attribute("product.id", str(args[1]))
                    
                elif operation_name == "list_products" and len(args) >= 2:
                    span.set_attribute("query.page", str(args[1].page))
                    span.set_attribute("query.page_size", str(args[1].page_size))
                    if args[1].q:
                        span.set_attribute("query.search", args[1].q)
                    if args[1].tags:
                        span.set_attribute("query.tags_count", str(len(args[1].tags)))
                    if args[1].min_price is not None:
                        span.set_attribute("query.min_price", str(args[1].min_price))
                    if args[1].max_price is not None:
                        span.set_attribute("query.max_price", str(args[1].max_price))
                        
                elif operation_name == "update_product" and len(args) >= 3:
                    span.set_attribute("product.id", str(args[1]))
                    span.set_attribute("product.name", args[2].name)
                    span.set_attribute("update.fields", str(list(args[2].model_dump().keys())))
                    
                elif operation_name == "patch_product" and len(args) >= 3:
                    span.set_attribute("product.id", str(args[1]))
                    span.set_attribute("patch.fields", str(list(args[2].model_dump(exclude_unset=True).keys())))
                    
                elif operation_name == "delete_product" and len(args) >= 2:
                    span.set_attribute("product.id", str(args[1]))
                    
                elif operation_name == "update_inventory" and len(args) >= 3:
                    span.set_attribute("product.id", str(args[1]))
                    span.set_attribute("inventory.new_stock", str(args[2].stock))
                    
                elif operation_name == "add_product_images" and len(args) >= 3:
                    span.set_attribute("product.id", str(args[1]))
                    span.set_attribute("image_files.count", len(args[2]))
                    
                elif operation_name == "remove_product_image" and len(args) >= 3:
                    span.set_attribute("product.id", str(args[1]))
                    span.set_attribute("image.url", str(args[2]))
                    
                elif operation_name == "update_product_tags" and len(args) >= 3:
                    span.set_attribute("product.id", str(args[1]))
                    span.set_attribute("tags.count", str(len(args[2].tags)))
                    
                elif operation_name == "cleanup_product_images" and len(args) >= 2:
                    span.set_attribute("product.id", str(args[1]))
                    
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator
