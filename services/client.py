import logging
from sqlalchemy.orm import Session
from models import Client

logger = logging.getLogger(__name__)


class ClientService:
    @staticmethod
    def create_client(db: Session, user_id: int, email: str, uuid: str, 
                     inbound_id: int, total_gb: int) -> Client:
        client = Client(
            user_id=user_id,
            email=email,
            uuid=uuid,
            inbound_id=inbound_id,
            status="active",
            total_gb=total_gb,
            used_gb=0
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        logger.info(f"Created client: {email} for user {user_id}")
        
        return client
    
    @staticmethod
    def get_user_clients(db: Session, user_id: int) -> list:
        return db.query(Client).filter(Client.user_id == user_id).all()
    
    @staticmethod
    def get_client_by_id(db: Session, client_id: int) -> Client:
        return db.query(Client).filter(Client.id == client_id).first()
    
    @staticmethod
    def get_client_by_email(db: Session, email: str) -> Client:
        return db.query(Client).filter(Client.email == email).first()
    
    @staticmethod
    def get_client_by_uuid(db: Session, uuid: str) -> Client:
        return db.query(Client).filter(Client.uuid == uuid).first()
    
    @staticmethod
    def update_client_status(db: Session, client_id: int, status: str) -> Client:
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if client:
            client.status = status
            db.commit()
            db.refresh(client)
            logger.info(f"Updated client {client_id} status to {status}")
        
        return client
    
    @staticmethod
    def update_client_usage(db: Session, client_id: int, used_gb: int) -> Client:
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if client:
            client.used_gb = used_gb
            if used_gb >= client.total_gb:
                client.status = "disabled"
            db.commit()
            db.refresh(client)
            logger.info(f"Updated client {client_id} usage: {used_gb}/{client.total_gb} GB")
        
        return client
    
    @staticmethod
    def delete_client(db: Session, client_id: int) -> bool:
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if client:
            db.delete(client)
            db.commit()
            logger.info(f"Deleted client {client_id}")
            return True
        
        return False
