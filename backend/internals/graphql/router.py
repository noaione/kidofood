"""
MIT License

Copyright (c) 2022-present noaione

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
from starlette import status
from strawberry.exceptions import MissingQueryError
from strawberry.fastapi import GraphQLRouter
from strawberry.http import parse_request_data
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types.graphql import OperationType

from internals.responses import ORJSONXResponse

__all__ = ("KidoGraphQLRouter",)


class KidoGraphQLRouter(GraphQLRouter):
    async def execute_request(self, request: Request, response: Response, data: dict, context, root_value) -> Response:
        try:
            request_data = parse_request_data(data)
        except MissingQueryError:
            missing_query_response = PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
            return self._merge_responses(response, missing_query_response)

        method = request.method
        allowed_operation_types = OperationType.from_http(method)

        if not self.allow_queries_via_get and method == "GET":
            allowed_operation_types = allowed_operation_types - {OperationType.QUERY}

        try:
            result = await self.execute(
                request_data.query,
                variables=request_data.variables,
                context=context,
                operation_name=request_data.operation_name,
                root_value=root_value,
                allowed_operation_types=allowed_operation_types,
            )
        except InvalidOperationTypeError as e:
            return PlainTextResponse(
                e.as_http_error_reason(method),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        response_data = await self.process_result(request, result)

        # <-- KidoFood: Change response to ORJSONXResponse
        actual_response: ORJSONXResponse = ORJSONXResponse(
            response_data,
            status_code=status.HTTP_200_OK,
        )
        # -->

        return self._merge_responses(response, actual_response)
