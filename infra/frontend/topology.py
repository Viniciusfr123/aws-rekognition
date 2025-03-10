import builtins
from infra.interfaces import IRflStack
from constructs import Construct
from aws_cdk import (
    aws_iam as iam,
    aws_cognito as cognito
)

class FaceLivenessCognito(Construct):
    '''
    Configuração do Cognito (User Pool, Identity Pool e Roles).
    '''
    def __init__(self, scope: Construct, id: builtins.str, rfl_stack: IRflStack) -> None:
        super().__init__(scope, id)

        # Criação do User Pool
        self.cognito = cognito.UserPool(
            self, "RFL-Cognito-User-Pool", 
            user_pool_name=rfl_stack.stack_name
            custom_attributes={
                "faceId": cognito.StringAttribute(mutable=True) #faceId
            }
        )

        # Client do User Pool (para aplicativos)
        self.client = cognito.UserPoolClient(
            self, "RFL-Cognito-Client", 
            user_pool=self.cognito, 
            user_pool_client_name=rfl_stack.stack_name
        )

        # Identity Pool (para acesso temporário a recursos AWS)
        self.idp = cognito.CfnIdentityPool(
            self, "RFL-IdentityPool", 
            identity_pool_name=rfl_stack.stack_name, 
            allow_unauthenticated_identities=True,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.client.user_pool_client_id, 
                    provider_name=self.cognito.user_pool_provider_name
                )
            ]
        )

        # Role para usuários não autenticados
        self.unAuthrole = iam.Role(
            self, 'RFLIdentityPoolUnAuthRole',
            assumed_by=iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com', 
                conditions={
                    "StringEquals": {"cognito-identity.amazonaws.com:aud": self.idp.ref},
                    "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "unauthenticated"}
                }, 
                assume_role_action='sts:AssumeRoleWithWebIdentity'
            ),
            description='Role para acesso não autenticado ao Rekognition',
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonRekognitionFullAccess')
            ]
        )

        # Vinculação da role ao Identity Pool
        self.idpAttachment = cognito.CfnIdentityPoolRoleAttachment(
            self, 'RFL-IdentityPool-Role-Attachment', 
            identity_pool_id=self.idp.ref, 
            roles={"unauthenticated": self.unAuthrole.role_arn}
        )

# import builtins
# from infra.interfaces import IRflStack
# from infra.facelivenessbackend.gateway.topology import FaceLivenessGateway
# from infra.frontend.cognito.topology import FaceLivenessCognito
# from constructs import Construct
# import aws_cdk as core
# from constructs import Construct
# from os import path
# from aws_cdk import (
#     CfnOutput,
#     aws_iam as iam,
#     aws_lambda as lambda_,
#     custom_resources as cr,
#     aws_codecommit as codecommit,
#     aws_amplify_alpha as amplify2
# )

# import aws_cdk.aws_s3_assets as s3_assets


# root_directory = path.dirname(__file__)
# bin_directory = path.join(root_directory, "bin")


# class FaceLivenessFrontEnd(Construct):
#     '''
#     Represents the root construct to create Amplify APP
#     '''

#     def __init__(self, scope: Construct, id: builtins.str, rfl_stack: IRflStack, apigateway: FaceLivenessGateway, cognito:FaceLivenessCognito) -> None:
#         super().__init__(scope, id)

#         s3_asset = s3_assets.Asset(self, "Rfl-Web-App-Code",
#                                    path="./src/frontend"
#                                    )
#         self.appRrepo = codecommit.Repository(self, "Rfl-Web-App-Repo",
#                                                     repository_name='{}-Repo'.format(
#                                                         rfl_stack.stack_name),
#                                                     code=codecommit.Code.from_asset(
#                                                         s3_asset)
#                                               )
#         self.amplify = amplify2.App(self, "Rfl-Web-App",
#                                     app_name=rfl_stack.stack_name,
#                                     auto_branch_creation=amplify2.AutoBranchCreation(
#                                         auto_build=True,
#                                         patterns=["main/*", "prod/*"],
#                                     ),
#                                     custom_rules=[amplify2.CustomRule(
#                                         source="</^((?!\.(css|gif|ico|jpg|js|png|txt|svg|woff|ttf)$).)*$/>",
#                                         target="/index.html",
#                                         status=amplify2.RedirectStatus.REWRITE
#                                     )],
#                                     source_code_provider=amplify2.CodeCommitSourceCodeProvider(
#                                         repository=self.appRrepo)
#                                     )
#         self.amplify.add_environment(
#             name="REACT_APP_ENV_API_URL", value=apigateway.rest_api_url())
#         self.amplify.add_environment(
#             name="REACT_APP_IDENTITYPOOL_ID", value=cognito.idp.ref)
#         self.amplify.add_environment(
#             name="REACT_APP_USERPOOL_ID", value=cognito.cognito.user_pool_id)
#         self.amplify.add_environment(
#             name="REACT_APP_WEBCLIENT_ID", value=cognito.client.user_pool_client_id)
#         self.amplify.add_environment(
#             name="REACT_APP_REGION", value=core.Stack.of(self).region)

#         self.amplify.add_branch("main", auto_build=True, branch_name="main")


# class TriggerFrontEndBuild(Construct):
#     '''
#     Represents the root construct for Triggering FE Aapp
#     '''

#     def __init__(self, scope: Construct, id: builtins.str, rfl_stack: IRflStack, amplifyApp: FaceLivenessFrontEnd) -> None:
#         super().__init__(scope, id)
#         self.triggerBuild = cr.AwsCustomResource(self, "Rfl-Web-App-Trigger-Build", policy=cr.AwsCustomResourcePolicy.from_sdk_calls(resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE),
#                                                  on_create=cr.AwsSdkCall(service="Amplify", action="startJob",
#                                                                          physical_resource_id=cr.PhysicalResourceId.of(
#                                                                              'app-build-trigger'),
#                                                                          parameters={
#                                                                              "appId": amplifyApp.amplify.app_id,
#                                                                              "branchName": "main",
#                                                                              "jobType": 'RELEASE',
#                                                                              "jobReason": 'Auto Start build',
#                                                                          }))


# class FaceLivenessFrontEndBuildStatus(Construct):
#     '''
#     Represents the root construct for FE APP build status
#     '''


#     def __init__(self, scope: Construct, id: builtins.str, rfl_stack: IRflStack, amplifyApp: FaceLivenessFrontEnd, buildTrigger: TriggerFrontEndBuild) -> None:
#         super().__init__(scope, id)
#         with open(f"./infra/frontend/amplifydeployment/index.py") as lambda_path:
#             code = lambda_path.read()

#         self.lambda_function = lambda_.Function(self, 'Rfl-Web-App-Lambda',
#                                                 function_name='{}-webapp-deployment'.format(
#                                                     rfl_stack.stack_name),
#                                                 code=lambda_.Code.from_inline(
#                                                     code),
#                                                 timeout=core.Duration.minutes(
#                                                     10),
#                                                 tracing=lambda_.Tracing.ACTIVE,
#                                                 runtime=lambda_.Runtime.PYTHON_3_9,
#                                                 handler='index.lambda_handler')

#         self.lambda_function.role.add_managed_policy(
#             iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationFullAccess'))

#         self.lambda_function.role.add_managed_policy(
#             iam.ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess-Amplify'))

#         input = "{\"app\":\""+rfl_stack.stack_name+"\",\"branch\":\"main\"}"

#         self.appStatus = cr.AwsCustomResource(self, id="Rfl-Web-App-Deploy-Status",
#                                               policy=cr.AwsCustomResourcePolicy.from_statements([
#                                                        iam.PolicyStatement(
#                                                            actions=[
#                                                                "lambda:InvokeFunction"],
#                                                            resources=[
#                                                                self.lambda_function.function_arn]
#                                                        )
#                                               ]),
#                                               on_create=cr.AwsSdkCall(service='Lambda', action='invoke',
#                                                                       physical_resource_id=cr.PhysicalResourceId.of('{}-webapp-stack'.format(
#                                                                           rfl_stack.stack_name)),
#                                                                       parameters={
#                                                                           'FunctionName': self.lambda_function.function_name,
#                                                                           "InvocationType": "RequestResponse",
#                                                                           "Payload": input
#                                                                       }),

#                                               on_update=cr.AwsSdkCall(service='Lambda', action='invoke',
#                                                                       physical_resource_id=cr.PhysicalResourceId.of('{}-webapp-stack'.format(
#                                                                           rfl_stack.stack_name)),
#                                                                       parameters={
#                                                                           'FunctionName': self.lambda_function.function_name,
#                                                                           "InvocationType": "RequestResponse",
#                                                                           "Payload": input
#                                                                       })
#                                               )
#         CfnOutput(self, id="RFL-Web-App-URL",
#                   value="https://main."+amplifyApp.amplify.app_id+".amplifyapp.com", export_name="RFL-Web-App-URL")
