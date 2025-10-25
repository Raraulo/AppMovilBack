from rolepermissions.roles import AbstractUserRole

class Admin(AbstractUserRole):
    available_permissions = {
        'gestionar_productos': True,
        'gestionar_clientes': True,
        'gestionar_facturas': True,
        'gestionar_usuarios': True,
    }

class Empleado(AbstractUserRole):
    available_permissions = {
        'gestionar_productos': True,
        'gestionar_clientes': True,
        'gestionar_facturas': True,
    }

class Cliente(AbstractUserRole):
    available_permissions = {
        'ver_productos': True,
        'realizar_compras': True,
    }
