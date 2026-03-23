import pulumi

pulumi.export("hello", pulumi.Config().require("hello"))
