from rest_framework import permissions

class ELojaOuSomenteLeitura(permissions.BasePermission):
    def tem_permissao(self, pedido, visualizacao):
        if pedido.method in permissions.SAFE_METHODS:
            return True
        return pedido.user.is_authenticated and pedido.user.loja

    def tem_objeto_permissao(self, pedido, visualizacao, objeto):
        if pedido.method in permissions.SAFE_METHODS:
            return True
        return objeto.loja == pedido.user
