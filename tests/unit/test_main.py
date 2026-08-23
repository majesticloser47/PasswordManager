from sesame import __main__ as main_module


class TestMain:
    def test_calls_typer_app(self, mocker):
        app_mock = mocker.patch.object(main_module, "app")

        main_module.main()

        app_mock.assert_called_once_with()
