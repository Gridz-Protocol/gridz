def test_server_module_registers_tools_without_error():
    from gridz_mcp import server

    assert server.mcp is not None
    assert callable(server.main)
