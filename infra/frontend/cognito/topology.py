import builtins
from infra.interfaces import IRflStack
from constructs import Construct
from os import path
from aws_cdk import (
    aws_iam as iam,
    aws_cognito as cognito,
    aws_logs as logs,
    custom_resources as cr
)


root_directory = path.dirname(__file__)
bin_directory = path.join(root_directory, "bin")


class FaceLivenessCognito(Construct):

    def __init__(self, scope: Construct, id: builtins.str, rfl_stack: IRflStack) -> None:
        super().__init__(scope, id)

        # Criando o User Pool do Cognito
        self.cognito = cognito.UserPool(
            self, "RFL-Cognito-User-Pool", user_pool_name=rfl_stack.stack_name
        )

        # Criando o Client do Cognito
        self.client = cognito.UserPoolClient(
            self, "RFL-Cognito-Client",
            user_pool=self.cognito,
            user_pool_client_name=rfl_stack.stack_name
        )

        # Criando o Identity Pool do Cognito
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

        # Criando a Role para usuários não autenticados
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

        # Anexando a Role ao Identity Pool
        self.idpAttachment = cognito.CfnIdentityPoolRoleAttachment(
            self, 'RFL-IdentityPool-Role-Attachment',
            identity_pool_id=self.idp.ref,
            roles={"unauthenticated": self.unAuthrole.role_arn}
        )

        # Criando a Collection no Rekognition usando um Custom Resource
        self.rekognition_collection = cr.AwsCustomResource(
            self, "CreateRekognitionCollection",
            on_create=cr.AwsSdkCall(
                service="Rekognition",
                action="CreateCollection",
                parameters={"CollectionId": "FaceAuthCollection"},
                physical_resource_id=cr.PhysicalResourceId.of("FaceAuthCollection")
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
            log_retention=logs.RetentionDays.ONE_WEEK
        )
