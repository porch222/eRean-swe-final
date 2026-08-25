import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

const ConfirmContext = createContext(null);

export function useConfirm() {
  const confirm = useContext(ConfirmContext);
  if (!confirm) throw new Error('useConfirm must be used inside <ConfirmProvider>');
  return confirm;
}

export function ConfirmProvider({ children }) {
  const [request, setRequest] = useState(null);
  const dialogRef = useRef(null);

  const resolveRef = useRef(null);

  const confirm = useCallback(
    (options) =>
      new Promise((resolve) => {
        resolveRef.current = resolve;
        setRequest(typeof options === 'string' ? { title: options } : options);
      }),
    [],
  );

  useEffect(() => {
    if (request) dialogRef.current?.showModal();
  }, [request]);

  function handleClose() {
    resolveRef.current?.(dialogRef.current?.returnValue === 'confirm');
    resolveRef.current = null;
    setRequest(null);
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {request && (
        <dialog ref={dialogRef} className="erean-modal" onClose={handleClose}>
          <form method="dialog" className="erean-modal__form">
            {request.eyebrow && <span className="erean-eyebrow">{request.eyebrow}</span>}
            <h2 className="erean-modal__title">{request.title}</h2>
            {request.body && <p className="erean-modal__body">{request.body}</p>}
            <div className="erean-modal__actions">

              <button type="submit" value="cancel" autoFocus className="btn btn-outline-secondary">
                {request.cancelLabel || 'Cancel'}
              </button>
              <button
                type="submit"
                value="confirm"
                className={`btn ${request.tone === 'danger' ? 'btn-danger' : 'btn-primary'}`}
              >
                {request.confirmLabel || 'Confirm'}
              </button>
            </div>
          </form>
        </dialog>
      )}
    </ConfirmContext.Provider>
  );
}
